<?php
error_reporting(0);
session_start();

$db = null;
try {
    $db = new mysqli('sqli_db', 'sroot', 'Sr00t_P@ssw0rd_2024!', 'news_db');
    if ($db->connect_error) throw new Exception();
    $db->set_charset('utf8mb4');
} catch (Exception $e) {
    die('<div style="text-align:center;padding:50px;font-family:sans-serif;"><h2>Database Connection Failed</h2><p>Please wait a moment and refresh...</p></div>');
}

$article = null;
$error = false;

if (isset($_GET['id'])) {
    $id = $_GET['id'];
    $sql = "SELECT a.*, c.name AS category_name FROM articles a
            LEFT JOIN categories c ON a.category_id = c.id
            WHERE a.id = $id";
    $result = $db->query($sql);
    if ($result && $result->num_rows > 0) {
        $article = $result->fetch_assoc();
    } else {
        $error = true;
    }
}

$latest_articles = [];
$res = $db->query("SELECT a.id, a.title, a.author, a.view_count, a.image_url, a.created_at, c.name AS category_name
                    FROM articles a LEFT JOIN categories c ON a.category_id = c.id
                    ORDER BY a.created_at DESC LIMIT 6");
if ($res) {
    while ($row = $res->fetch_assoc()) {
        $latest_articles[] = $row;
    }
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日资讯 - 让信息创造价值</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f4f5f7; color: #333; }

        .top-bar {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 8px 0;
            font-size: 13px;
        }
        .top-bar .container { display: flex; justify-content: space-between; align-items: center; }
        .top-bar a { color: #ccc; text-decoration: none; margin-left: 15px; transition: color 0.2s; }
        .top-bar a:hover { color: white; }
        .top-bar .datetime { color: #aaa; }

        header {
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        header .container { display: flex; align-items: center; padding: 0 20px; }
        .logo {
            font-size: 26px;
            font-weight: 800;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 16px 0;
            margin-right: 40px;
        }
        .logo span { font-size: 14px; font-weight: 400; -webkit-text-fill-color: #999; margin-left: 4px; }
        nav { display: flex; gap: 0; }
        nav a {
            display: block;
            padding: 20px 18px;
            color: #555;
            text-decoration: none;
            font-size: 15px;
            font-weight: 500;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }
        nav a:hover, nav a.active { color: #e74c3c; border-bottom-color: #e74c3c; }
        .header-right { margin-left: auto; display: flex; align-items: center; gap: 12px; }
        .header-right a { color: #888; text-decoration: none; font-size: 13px; }
        .header-right a:hover { color: #e74c3c; }
        .admin-link { background: #e74c3c; color: white !important; padding: 6px 14px; border-radius: 4px; }
        .admin-link:hover { background: #c0392b !important; color: white !important; }

        .container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }

        .banner {
            background: linear-gradient(135deg, #2c3e50, #1a252f);
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
            height: 260px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .banner-content { position: relative; z-index: 2; text-align: center; color: white; padding: 20px; }
        .banner-content h2 { font-size: 28px; margin-bottom: 10px; }
        .banner-content p { font-size: 15px; color: #aaa; }
        .banner::after {
            content: '';
            position: absolute;
            inset: 0;
            background: url('https://picsum.photos/seed/newsbanner/1200/260') center/cover no-repeat;
            opacity: 0.25;
        }

        .main-content { display: grid; grid-template-columns: 1fr 340px; gap: 24px; margin: 20px 0; }

        .section-title {
            font-size: 20px;
            font-weight: 700;
            padding-bottom: 10px;
            border-bottom: 3px solid #e74c3c;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .section-title a { font-size: 13px; color: #999; text-decoration: none; font-weight: 400; }
        .section-title a:hover { color: #e74c3c; }

        .article-detail { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
        .article-detail img { width: 100%; height: 400px; object-fit: cover; display: block; }
        .article-detail .body { padding: 28px 32px; }
        .article-detail .meta { font-size: 13px; color: #999; margin-bottom: 12px; display: flex; gap: 16px; align-items: center; }
        .article-detail .meta .cat { background: #fee; color: #c0392b; padding: 2px 10px; border-radius: 20px; font-size: 12px; }
        .article-detail h1 { font-size: 26px; line-height: 1.4; margin-bottom: 16px; color: #222; }
        .article-detail .content { font-size: 15px; line-height: 1.9; color: #444; }
        .article-detail .content p { margin-bottom: 14px; }
        .back-btn { display: inline-block; margin-top: 20px; color: #e74c3c; text-decoration: none; font-size: 14px; }
        .back-btn:hover { text-decoration: underline; }

        .error-box { background: white; border-radius: 8px; padding: 60px 40px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
        .error-box h3 { font-size: 18px; color: #999; margin-bottom: 20px; }
        .error-box a { color: #e74c3c; text-decoration: none; }

        .article-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.06); margin-bottom: 16px; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; }
        .article-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
        .article-card a { text-decoration: none; color: inherit; display: block; }
        .article-card .img-wrap { height: 160px; overflow: hidden; }
        .article-card img { width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s; }
        .article-card:hover img { transform: scale(1.05); }
        .article-card .card-body { padding: 14px 16px; }
        .article-card .card-cat { font-size: 12px; color: #c0392b; font-weight: 600; margin-bottom: 6px; }
        .article-card .card-title { font-size: 15px; font-weight: 700; color: #222; margin-bottom: 8px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .article-card .card-meta { font-size: 12px; color: #aaa; display: flex; justify-content: space-between; }
        .article-card .card-meta .views { color: #e74c3c; }

        .sidebar-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.06);
            margin-bottom: 16px;
        }
        .sidebar-card h4 { font-size: 15px; font-weight: 700; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eee; }
        .rank-item { display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid #f5f5f5; }
        .rank-item:last-child { border-bottom: none; }
        .rank-num { width: 20px; height: 20px; background: #e74c3c; color: white; border-radius: 50%; font-size: 11px; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 10px; flex-shrink: 0; }
        .rank-num.n2 { background: #e67e22; }
        .rank-num.n3 { background: #f39c12; }
        .rank-item a { font-size: 13px; color: #333; text-decoration: none; flex: 1; }
        .rank-item a:hover { color: #e74c3c; }
        .rank-item .rank-views { font-size: 12px; color: #ccc; margin-left: 8px; }

        .hot-tags { display: flex; flex-wrap: wrap; gap: 6px; }
        .hot-tags span { background: #f5f5f5; color: #666; padding: 4px 12px; border-radius: 20px; font-size: 12px; cursor: pointer; transition: all 0.2s; }
        .hot-tags span:hover { background: #e74c3c; color: white; }

        .source-note {
            text-align: center;
            font-size: 11px;
            color: #bbb;
            padding: 20px 0 8px;
            border-top: 1px solid #eee;
            margin-top: 10px;
        }

        footer { background: #1a1a2e; color: #888; padding: 30px 0; margin-top: 40px; font-size: 13px; }
        footer .container { display: flex; justify-content: space-between; align-items: center; }
        footer a { color: #888; text-decoration: none; }
        footer a:hover { color: #e74c3c; }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="container">
            <div class="datetime" id="datetime"></div>
            <div>
                <a href="#">订阅</a>
                <a href="#">客户端</a>
                <a href="/admin/">后台管理</a>
            </div>
        </div>
    </div>

    <header>
        <div class="container">
            <div class="logo">每日资讯<span>DailyNews</span></div>
            <nav>
                <a href="/" class="active">首页</a>
                <a href="#">科技</a>
                <a href="#">财经</a>
                <a href="#">体育</a>
                <a href="#">娱乐</a>
                <a href="#">国际</a>
            </nav>
            <div class="header-right">
                <a href="#">登录</a>
                <a href="/admin/" class="admin-link">后台</a>
            </div>
        </div>
    </header>

    <div class="container">
        <?php if ($article !== null): ?>
            <div class="article-detail" style="margin: 20px 0;">
                <?php if ($article['image_url']): ?>
                <img src="<?php echo htmlspecialchars($article['image_url']); ?>" alt="">
                <?php endif; ?>
                <div class="body">
                    <div class="meta">
                        <span class="cat"><?php echo htmlspecialchars($article['category_name']); ?></span>
                        <span><?php echo htmlspecialchars($article['author']); ?></span>
                        <span><?php echo date('Y-m-d H:i', strtotime($article['created_at'])); ?></span>
                        <span style="color:#e74c3c;"><?php echo (int)$article['view_count']; ?> 阅读</span>
                    </div>
                    <h1><?php echo htmlspecialchars($article['title']); ?></h1>
                    <div class="content">
                        <?php foreach (explode("\n", $article['content']) as $para): ?>
                            <?php if (trim($para)): ?>
                            <p><?php echo htmlspecialchars($para); ?></p>
                            <?php endif; ?>
                        <?php endforeach; ?>
                    </div>
                    <a href="/" class="back-btn">← 返回首页</a>
                </div>
            </div>
        <?php elseif ($error): ?>
            <div class="error-box">
                <h3>该文章不存在或已被删除</h3>
                <a href="/">← 返回首页</a>
            </div>
        <?php else: ?>
            <div class="banner">
                <div class="banner-content">
                    <h2>让信息创造价值</h2>
                    <p>每日资讯 · 专注科技 · 财经 · 体育 · 娱乐资讯平台</p>
                </div>
            </div>

            <div class="main-content">
                <div>
                    <div class="section-title">最新资讯</div>
                    <?php foreach ($latest_articles as $a): ?>
                    <div class="article-card">
                        <a href="/?id=<?php echo $a['id']; ?>">
                            <div class="img-wrap">
                                <img src="<?php echo htmlspecialchars($a['image_url']); ?>" alt="">
                            </div>
                            <div class="card-body">
                                <div class="card-cat"><?php echo htmlspecialchars($a['category_name']); ?></div>
                                <div class="card-title"><?php echo htmlspecialchars($a['title']); ?></div>
                                <div class="card-meta">
                                    <span><?php echo htmlspecialchars($a['author']); ?></span>
                                    <span class="views"><?php echo number_format($a['view_count']); ?> 阅读</span>
                                </div>
                            </div>
                        </a>
                    </div>
                    <?php endforeach; ?>
                </div>

                <div class="sidebar">
                    <div class="sidebar-card">
                        <h4>热门文章</h4>
                        <?php
                        $hot = $db->query("SELECT id, title, view_count FROM articles ORDER BY view_count DESC LIMIT 5");
                        $rank = 1;
                        while ($h = $hot->fetch_assoc()):
                        ?>
                        <div class="rank-item">
                            <div class="rank-num <?php if($rank==2) echo 'n2'; if($rank==3) echo 'n3'; ?>"><?php echo $rank; ?></div>
                            <a href="/?id=<?php echo $h['id']; ?>"><?php echo htmlspecialchars($h['title']); ?></a>
                            <span class="rank-views"><?php echo $h['view_count']; ?></span>
                        </div>
                        <?php $rank++; endwhile; ?>
                    </div>

                    <div class="sidebar-card">
                        <h4>热门标签</h4>
                        <div class="hot-tags">
                            <span>AI</span><span>GPT-5</span><span>A股</span><span>女排</span>
                            <span>电影</span><span>欧盟</span><span>科幻</span><span>碳中和</span>
                            <span>世界杯</span><span>电动车</span>
                        </div>
                    </div>

                    <div class="sidebar-card" style="background:linear-gradient(135deg,#2c3e50,#1a252f);color:white;">
                        <h4 style="border-bottom-color:#444;color:white;">关于我们</h4>
                        <p style="font-size:13px;line-height:1.8;color:#aaa;margin-top:8px;">
                            每日资讯（DailyNews）成立于2020年，<br>
                            致力于为用户提供及时、权威、有价值的资讯服务。
                        </p>
                        <p style="font-size:11px;color:#666;margin-top:12px;">源自某SRC真实场景</p>
                    </div>
                </div>
            </div>
        <?php endif; ?>

        <div class="source-note">每日资讯 DailyNews · 版权声明 · 联系我们</div>
    </div>

    <footer>
        <div class="container">
            <div>© 2024 每日资讯 DailyNews 版权所有</div>
            <div>
                <a href="#">关于我们</a>&nbsp;&nbsp;
                <a href="#">隐私政策</a>&nbsp;&nbsp;
                <a href="/admin/">管理后台</a>
            </div>
        </div>
    </footer>

    <script>
        function updateTime() {
            var now = new Date();
            var s = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0') + ' ' + String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0') + ':' + String(now.getSeconds()).padStart(2,'0');
            document.getElementById('datetime').textContent = s;
        }
        updateTime();
        setInterval(updateTime, 1000);
    </script>
</body>
</html>
