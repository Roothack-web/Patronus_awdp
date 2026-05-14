<?php
error_reporting(0);
session_start();
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header('Location: login.php');
    exit;
}

$msg = '';
$msg_type = 'success';
$template_dir = '/var/www/html/templates/';

if (!is_dir($template_dir)) {
    mkdir($template_dir, 0755, true);
}

$templates = ['header', 'footer', 'article_card', 'sidebar', 'index_main'];
$current_template = isset($_POST['template']) ? $_POST['template'] : 'header';
$default_content = [
    'header' => "<!-- Header Template -->\n<header>\n    <nav>\n        <a href=\"/\">首页</a>\n        <a href=\"/category/tech\">科技</a>\n        <a href=\"/category/finance\">财经</a>\n    </nav>\n</header>",
    'footer' => "<!-- Footer Template -->\n<footer>\n    <p>&copy; 2024 每日资讯 DailyNews</p>\n</footer>",
    'article_card' => "<!-- Article Card Template -->\n<div class=\"article-card\">\n    <h3><?= \$title ?></h3>\n    <p><?= \$summary ?></p>\n</div>",
    'sidebar' => "<!-- Sidebar Template -->\n<aside class=\"sidebar\">\n    <div class=\"widget\">热门文章</div>\n</aside>",
    'index_main' => "<!-- Index Main Content Template -->\n<div class=\"main-content\">\n    <?php include 'banner.php'; ?>\n    <div class=\"article-list\">\n        <?php foreach (\$articles as \$a): ?>\n        <div class=\"card\"><?= \$a['title'] ?></div>\n        <?php endforeach; ?>\n    </div>\n</div>",
];

$file_path = $template_dir . $current_template . '.php';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'save') {
    $content = $_POST['content'] ?? '';
    $selected = $_POST['template'] ?? 'header';
    $target = $template_dir . $selected . '.php';
    if (file_put_contents($target, $content) !== false) {
        $msg = "模板 \"{$selected}\" 保存成功！";
        $msg_type = 'success';
        $current_template = $selected;
        $file_path = $target;
    } else {
        $msg = "保存失败，请检查目录权限。";
        $msg_type = 'error';
    }
}

$current_content = file_exists($file_path) ? file_get_contents($file_path) : ($default_content[$current_template] ?? '');
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>模板编辑 - 每日资讯</title>
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
        .container { max-width: 1100px; margin: 30px auto; padding: 0 20px; }
        .panel { background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        .panel-header { padding: 16px 24px; border-bottom: 1px solid #eee; display: flex; align-items: center; justify-content: space-between; }
        .panel-header h3 { font-size: 15px; font-weight: 700; }
        .panel-body { padding: 24px; }
        .form-row { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 16px; }
        .form-row label { display: block; font-size: 14px; font-weight: 600; color: #333; min-width: 60px; padding-top: 8px; }
        select, input[type="text"] {
            padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 6px;
            font-size: 14px; font-family: inherit;
        }
        select:focus, input:focus { outline: none; border-color: #0f3460; }
        .editor-wrap { position: relative; }
        textarea {
            width: 100%; min-height: 420px;
            border: 2px solid #e0e0e0; border-radius: 6px;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 13px; line-height: 1.6;
            padding: 14px; resize: vertical;
            background: #1e1e1e; color: #d4d4d4;
            tab-size: 4;
        }
        textarea:focus { outline: none; border-color: #0f3460; }
        .btn-row { display: flex; gap: 10px; margin-top: 16px; justify-content: flex-end; }
        .btn {
            padding: 10px 24px; border: none; border-radius: 6px;
            font-size: 14px; font-weight: 600; cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.85; }
        .btn-primary { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }
        .btn-secondary { background: #f0f0f0; color: #555; }
        .btn-preview { background: linear-gradient(135deg, #0f3460, #1a1a2e); color: white; }
        .msg {
            padding: 12px 16px; border-radius: 6px; font-size: 14px; margin-bottom: 16px;
        }
        .msg.success { background: #f0fff4; border: 1px solid #bbf7d0; color: #155724; }
        .msg.error { background: #fff0f0; border: 1px solid #fcc; color: #c0392b; }
        .tip { font-size: 12px; color: #999; margin-top: 8px; }
        .tip code { background: #f5f5f5; padding: 1px 5px; border-radius: 3px; color: #c0392b; font-family: monospace; }
        .preview-box { margin-top: 16px; border: 1px solid #eee; border-radius: 6px; background: #fafafa; padding: 16px; display: none; }
        .preview-box.active { display: block; }
    </style>
</head>
<body>
    <div class="header">
        <div class="title">每日资讯 · 管理后台</div>
        <div class="user">
            欢迎，<?php echo htmlspecialchars($_SESSION['admin_user'] ?? 'admin'); ?> &nbsp;|&nbsp; <a href="?action=logout">退出</a>
        </div>
    </div>
    <div class="nav">
        <a href="/admin/index.php">概况</a>
        <a href="/admin/article.php">文章管理</a>
        <a href="/admin/category.php">分类管理</a>
        <a href="/admin/template.php" class="active">模板编辑</a>
        <a href="/admin/settings.php">系统设置</a>
    </div>
    <div class="container">
        <div class="panel">
            <div class="panel-header">
                <h3>模板文件编辑</h3>
                <span style="font-size:12px;color:#999;">当前文件: <code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-family:monospace;">/templates/<?php echo htmlspecialchars($current_template); ?>.php</code></span>
            </div>
            <div class="panel-body">
                <?php if ($msg): ?>
                <div class="msg <?php echo $msg_type; ?>"><?php echo htmlspecialchars($msg); ?></div>
                <?php endif; ?>

                <form method="POST" action="">
                    <div class="form-row">
                        <label>模板</label>
                        <select name="template" onchange="this.form.submit()">
                            <?php foreach ($templates as $t): ?>
                            <option value="<?php echo $t; ?>" <?php if ($current_template === $t) echo 'selected'; ?>><?php echo $t; ?>.php</option>
                            <?php endforeach; ?>
                        </select>
                    </div>
                    <div class="editor-wrap">
                        <textarea name="content" id="editor" spellcheck="false"><?php echo htmlspecialchars($current_content); ?></textarea>
                    </div>
                    <p class="tip">💡 直接写入 PHP 文件，请谨慎操作。保存后可在 <code>/templates/xxx.php</code> 访问。</p>
                    <div class="btn-row">
                        <button type="button" class="btn btn-preview" onclick="togglePreview()">👁 预览</button>
                        <button type="submit" name="action" value="save" class="btn btn-primary">💾 保存模板</button>
                    </div>
                </form>

                <div class="preview-box" id="previewBox">
                    <strong style="font-size:13px;color:#666;">渲染预览：</strong>
                    <pre id="previewContent" style="margin-top:8px;background:#f5f5f5;padding:12px;border-radius:4px;font-size:12px;font-family:monospace;max-height:200px;overflow:auto;"></pre>
                </div>
            </div>
        </div>
    </div>

    <script>
        function togglePreview() {
            var box = document.getElementById('previewBox');
            var content = document.getElementById('previewContent');
            if (box.classList.contains('active')) {
                box.classList.remove('active');
            } else {
                box.classList.add('active');
                content.textContent = document.getElementById('editor').value;
            }
        }
        document.getElementById('editor').addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                var start = this.selectionStart;
                var end = this.selectionEnd;
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });
    </script>
</body>
</html>
