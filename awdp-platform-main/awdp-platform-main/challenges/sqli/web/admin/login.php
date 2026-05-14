<?php
error_reporting(0);
session_start();
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $db = new mysqli('sqli_db', 'sroot', 'Sr00t_P@ssw0rd_2024!', 'news_db');
    $db->set_charset('utf8mb4');
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';
    $sql = "SELECT * FROM admins WHERE (username = '$username') AND (password = '" . md5($password) . "')";
    $res = $db->query($sql);
    if ($res && $res->num_rows > 0) {
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_user'] = $username;
        header('Location: /admin/index.php');
        exit;
    } else {
        $error = '用户名或密码错误';
    }
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>后台登录 - 每日资讯</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-box {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            padding: 48px 40px;
            width: 400px;
        }
        .login-box h2 { text-align: center; color: #1a1a2e; margin-bottom: 8px; font-size: 24px; }
        .login-box .sub { text-align: center; color: #999; font-size: 13px; margin-bottom: 32px; }
        .form-group { margin-bottom: 18px; }
        .form-group label { display: block; font-size: 14px; color: #333; font-weight: 600; margin-bottom: 6px; }
        .form-group input {
            width: 100%; padding: 11px 14px;
            border: 2px solid #e0e0e0; border-radius: 6px;
            font-size: 14px; font-family: inherit;
            transition: border-color 0.2s;
        }
        .form-group input:focus { outline: none; border-color: #0f3460; }
        .btn {
            width: 100%; padding: 12px;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            color: white; border: none; border-radius: 6px;
            font-size: 15px; font-weight: 600; cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.9; }
        .error-msg {
            background: #fff0f0; border: 1px solid #fcc;
            color: #c0392b; padding: 10px 14px; border-radius: 6px;
            font-size: 13px; margin-bottom: 16px;
        }
        .back-home { text-align: center; margin-top: 20px; }
        .back-home a { color: #999; text-decoration: none; font-size: 13px; }
        .back-home a:hover { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>管理后台</h2>
        <p class="sub">每日资讯 · DailyNews</p>
        <?php if (!empty($error)): ?>
        <div class="error-msg"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>
        <form method="POST" action="login.php">
            <div class="form-group">
                <label>用户名</label>
                <input type="text" name="username" placeholder="请输入用户名" required>
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" placeholder="请输入密码" required>
            </div>
            <button type="submit" class="btn">登录</button>
        </form>
        <div class="back-home">
            <a href="/">← 返回首页</a>
        </div>
    </div>
</body>
</html>
