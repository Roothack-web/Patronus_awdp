<?php
error_reporting(0);
session_start();
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header('Location: login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>文章管理 - 每日资讯</title>
    <style>
        body { font-family: 'PingFang SC', sans-serif; background: #f0f2f5; margin: 0; }
        .header { background: #1a1a2e; color: white; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 56px; }
        .header .title { font-size: 18px; font-weight: 700; }
        .header .user a { color: #e74c3c; text-decoration: none; font-size: 13px; }
        .nav { background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.08); padding: 0 24px; display: flex; }
        .nav a { display: block; padding: 14px 20px; color: #555; text-decoration: none; font-size: 14px; border-bottom: 2px solid transparent; }
        .nav a:hover, .nav a.active { color: #e74c3c; border-bottom-color: #e74c3c; }
        .container { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
        .panel { background: white; border-radius: 8px; padding: 24px; }
        .panel h3 { margin: 0 0 16px; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
        .coming { text-align: center; padding: 60px; color: #ccc; font-size: 18px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">每日资讯 · 管理后台</div>
        <div class="user">欢迎，<?php echo htmlspecialchars($_SESSION['admin_user']); ?> &nbsp;|&nbsp; <a href="?action=logout">退出</a></div>
    </div>
    <div class="nav">
        <a href="/admin/index.php">概况</a>
        <a href="/admin/article.php" class="active">文章管理</a>
        <a href="/admin/category.php">分类管理</a>
        <a href="/admin/template.php">模板编辑</a>
        <a href="/admin/settings.php">系统设置</a>
    </div>
    <div class="container">
        <div class="panel">
            <h3>文章管理</h3>
            <div class="coming">功能开发中...</div>
        </div>
    </div>
</body>
</html>
