<?php
error_reporting(0);
session_start();
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header('Location: login.php');
    exit;
}
$username = $_SESSION['admin_user'] ?? 'admin';

if (isset($_GET['action']) && $_GET['action'] === 'logout') {
    session_destroy();
    header('Location: login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>后台管理 - 每日资讯</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f0f2f5; color: #333; }
        .header { background: #1a1a2e; color: white; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; height: 56px; }
        .header .title { font-size: 18px; font-weight: 700; }
        .header .user { font-size: 13px; color: #aaa; }
        .header .user a { color: #e74c3c; text-decoration: none; }
        .nav { background: white; box-shadow: 0 1px 4px rgba(0,0,0,0.08); padding: 0 24px; display: flex; gap: 0; }
        .nav a { display: block; padding: 14px 20px; color: #555; text-decoration: none; font-size: 14px; border-bottom: 2px solid transparent; transition: all 0.2s; }
        .nav a:hover, .nav a.active { color: #e74c3c; border-bottom-color: #e74c3c; }
        .container { max-width: 1000px; margin: 30px auto; padding: 0 20px; }
        .panel { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 24px; margin-bottom: 20px; }
        .panel h3 { font-size: 16px; font-weight: 700; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
        .stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
        .stat-card { background: linear-gradient(135deg, #1a1a2e, #0f3460); color: white; border-radius: 8px; padding: 20px; text-align: center; }
        .stat-card.n2 { background: linear-gradient(135deg, #e74c3c, #c0392b); }
        .stat-card.n3 { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .stat-card.n4 { background: linear-gradient(135deg, #e67e22, #f39c12); }
        .stat-card .num { font-size: 28px; font-weight: 800; }
        .stat-card .label { font-size: 13px; color: rgba(255,255,255,0.8); margin-top: 4px; }
        .menu-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        .menu-item { background: #f8f9fa; border: 1px solid #eee; border-radius: 6px; padding: 16px; text-align: center; cursor: pointer; text-decoration: none; color: #333; font-size: 14px; transition: all 0.2s; }
        .menu-item:hover { border-color: #e74c3c; color: #e74c3c; background: #fff5f5; }
        .menu-item .icon { font-size: 24px; margin-bottom: 6px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">每日资讯 · 管理后台</div>
        <div class="user">
            欢迎，<?php echo htmlspecialchars($username); ?> &nbsp;|&nbsp; <a href="?action=logout">退出</a>
        </div>
    </div>
    <div class="nav">
        <a href="/admin/index.php" class="active">概况</a>
        <a href="/admin/article.php">文章管理</a>
        <a href="/admin/category.php">分类管理</a>
        <a href="/admin/template.php">模板编辑</a>
        <a href="/admin/settings.php">系统设置</a>
    </div>
    <div class="container">
        <div class="stat-grid">
            <div class="stat-card">
                <div class="num">5</div>
                <div class="label">文章总数</div>
            </div>
            <div class="stat-card n2">
                <div class="num">66K</div>
                <div class="label">总阅读量</div>
            </div>
            <div class="stat-card n3">
                <div class="num">5</div>
                <div class="label">分类数量</div>
            </div>
            <div class="stat-card n4">
                <div class="num">1</div>
                <div class="label">管理员</div>
            </div>
        </div>
        <div class="panel" style="margin-top:20px;">
            <h3>快捷功能</h3>
            <div class="menu-grid">
                <a class="menu-item" href="/admin/article.php">
                    <div class="icon">📝</div>文章管理
                </a>
                <a class="menu-item" href="/admin/category.php">
                    <div class="icon">📁</div>分类管理
                </a>
                <a class="menu-item" href="/admin/template.php">
                    <div class="icon">🎨</div>模板编辑
                </a>
                <a class="menu-item" href="/admin/settings.php">
                    <div class="icon">⚙️</div>系统设置
                </a>
                <a class="menu-item" href="/admin/user.php">
                    <div class="icon">👤</div>用户管理
                </a>
                <a class="menu-item" href="/">
                    <div class="icon">🏠</div>返回前台
                </a>
            </div>
        </div>
    </div>
</body>
</html>
