<?php
error_reporting(0);
session_start();

// 题目：SSRF + 无防护版本
// [Player] --HTTP--> [web1:80] --SSRF--> [web2:8080]

function ssrf_request($url, $method = 'GET', $post_data = '', $timeout = 5) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, $timeout);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, false);
    curl_setopt($ch, CURLOPT_USERAGENT, 'PHP SSRF Client');
    curl_setopt($ch, CURLOPT_HEADER, false);

    if ($method === 'POST' && $post_data !== '') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post_data);
    }

    $response = curl_exec($ch);
    $httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error    = curl_error($ch);
    curl_close($ch);
    return ['code' => $httpcode, 'body' => $response, 'error' => $error];
}

// 处理请求
$result = null;
if (isset($_GET['url'])) {
    $url      = $_GET['url'];
    $method   = isset($_GET['method']) ? $_GET['method'] : 'GET';
    $post_data = isset($_GET['post_data']) ? $_GET['post_data'] : '';
    $result   = ssrf_request($url, $method, $post_data);
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>内网资源管理器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex; justify-content: center; align-items: center; padding: 20px;
        }
        .container {
            background: rgba(255,255,255,0.95);
            border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            padding: 40px; width: 100%; max-width: 800px;
        }
        h1 { color: #1a1a2e; margin-bottom: 10px; text-align: center; font-size: 26px; }
        .subtitle { color: #555; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 600; }
        input[type="text"], select, textarea {
            width: 100%; padding: 12px 16px;
            border: 2px solid #e0e0e0; border-radius: 6px;
            font-size: 15px; font-family: 'Courier New', monospace;
            transition: border-color 0.3s; background: #fff;
        }
        input[type="text"]:focus, select:focus, textarea:focus { outline: none; border-color: #0f3460; }
        textarea { resize: vertical; min-height: 100px; }
        .btn-row { display: flex; gap: 10px; }
        button {
            flex: 1; padding: 12px;
            background: linear-gradient(135deg, #1a1a2e, #0f3460);
            color: white; border: none; border-radius: 6px;
            font-size: 15px; font-weight: 600; cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(15,52,96,0.4); }
        .response-box { margin-top: 25px; }
        .response-title { font-weight: 600; margin-bottom: 8px; color: #333; font-size: 14px; }
        .response-meta { display: flex; gap: 15px; margin-bottom: 10px; }
        .meta-item { background: #f0f0f0; padding: 4px 12px; border-radius: 4px; font-size: 13px; font-family: 'Courier New', monospace; }
        .response-body {
            background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 6px;
            font-family: 'Courier New', monospace; font-size: 13px;
            white-space: pre-wrap; word-break: break-all;
            max-height: 400px; overflow-y: auto; border: 1px solid #333;
        }
        .error-body { background: #2d1f1f; color: #ff6b6b; border: 1px solid #5c2b2b; }
        .hint {
            margin-top: 25px; padding: 15px;
            background-color: #fff3cd; border: 1px solid #ffeeba;
            border-radius: 6px; color: #856404; font-size: 13px;
        }
        .hint strong { display: block; margin-bottom: 5px; }
        .top-bar {
            text-align: center; margin-bottom: 20px;
            padding-bottom: 15px; border-bottom: 2px solid #f0f0f0;
        }
        .top-bar span {
            display: inline-block; background: linear-gradient(135deg, #1a1a2e, #0f3460);
            color: white; padding: 4px 16px; border-radius: 20px;
            font-size: 12px; font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <span>[ Player ] --HTTP--> [ 本机:80 ] --SSRF--> [ web2:8080 ]</span>
        </div>
        <h1>内网和远方</h1>
        <p class="subtitle">内网和远方，究竟哪一个可以到达呢？</p>

        <form method="GET" action="">
            <div class="form-group">
                <label for="url">请求地址</label>
                <input type="text" id="url" name="url"
                       placeholder="http://127.0.0.1:8080/xxxxx"
                       value="<?php echo isset($_GET['url']) ? htmlspecialchars($_GET['url']) : ''; ?>"
                       required>
            </div>
            <div class="form-group">
                <label for="method">请求方法</label>
                <select id="method" name="method" onchange="togglePostData()">
                    <option value="GET" <?php echo (isset($_GET['method']) && $_GET['method'] === 'POST') ? '' : 'selected'; ?>>GET</option>
                    <option value="POST" <?php echo (isset($_GET['method']) && $_GET['method'] === 'POST') ? 'selected' : ''; ?>>POST</option>
                </select>
            </div>
            <div class="form-group" id="post_data_group" style="<?php echo (isset($_GET['method']) && $_GET['method'] === 'POST') ? '' : 'display:none'; ?>">
                <label for="post_data">POST 数据</label>
                <textarea id="post_data" name="post_data" placeholder="key1=value1&key2=value2"><?php echo isset($_GET['post_data']) ? htmlspecialchars($_GET['post_data']) : ''; ?></textarea>
            </div>
            <div class="btn-row">
                <button type="submit">发送请求</button>
            </div>
        </form>

        <?php if ($result !== null): ?>
        <div class="response-box">
            <div class="response-title">响应结果</div>
            <div class="response-meta">
                <span class="meta-item">HTTP <?php echo $result['code']; ?></span>
                <?php if ($result['error']): ?>
                <span class="meta-item" style="background:#ffdddd;color:#cc0000;">ERR: <?php echo htmlspecialchars($result['error']); ?></span>
                <?php endif; ?>
            </div>
            <iframe id="responseFrame" name="responseFrame"
                    srcdoc="<?php echo htmlspecialchars($result['body']); ?>"
                    sandbox="allow-same-origin allow-scripts allow-top-navigation"
                    style="width:100%; min-height:400px; border:1px solid #333; border-radius:6px; background:#fff;">
            </iframe>
        </div>
        <?php endif; ?>

    </div>

    <script>
        function togglePostData() {
            var method = document.getElementById('method').value;
            document.getElementById('post_data_group').style.display = (method === 'POST') ? '' : 'none';
        }
    </script>
</body>
</html>
