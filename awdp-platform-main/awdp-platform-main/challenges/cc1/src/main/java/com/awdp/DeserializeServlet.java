package com.awdp;

import java.io.*;
import java.util.Base64;
import javax.servlet.*;
import javax.servlet.http.*;

/**
 * Vulnerable servlet — deserializes base64-decoded user input via ObjectInputStream.
 * CC1 (CommonsCollections1) gadget chain can achieve RCE.
 */
public class DeserializeServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws IOException {
        resp.setContentType("text/html;charset=utf-8");
        PrintWriter w = resp.getWriter();
        w.println("<h1>CC1 Deserialization Challenge</h1>");
        w.println("<p>POST base64-encoded serialized Java object to /deserialize</p>");
        w.println("<p>Hint: CommonsCollections 3.1 + CC1 chain</p>");
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws IOException {
        String path = req.getServletPath();

        if ("/deserialize".equals(path)) {
            try {
                // Read base64-encoded body
                BufferedReader reader = req.getReader();
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                byte[] data = Base64.getDecoder().decode(sb.toString().trim());

                // VULNERABLE: deserialize without any validation
                ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(data));
                Object obj = ois.readObject();
                resp.getWriter().write("ok: " + obj.getClass().getName());
            } catch (ClassNotFoundException e) {
                resp.getWriter().write("error: " + e.getMessage());
            } catch (IOException e) {
                resp.getWriter().write("error: " + e.getMessage());
            }
        } else {
            resp.sendError(404);
        }
    }
}
