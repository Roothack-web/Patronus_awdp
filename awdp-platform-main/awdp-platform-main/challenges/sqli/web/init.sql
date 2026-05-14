SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE IF NOT EXISTS `admins` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `password` VARCHAR(32) NOT NULL,
    `email` VARCHAR(100),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `categories` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL,
    `description` VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS `articles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(200) NOT NULL,
    `content` TEXT NOT NULL,
    `category_id` INT,
    `author` VARCHAR(50),
    `view_count` INT DEFAULT 0,
    `image_url` VARCHAR(255),
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT IGNORE INTO `admins` (`username`, `password`, `email`) VALUES
('admin', 'b868b0cd65898b963a906b14dadc9858', 'admin@news-site.com');

INSERT IGNORE INTO `categories` (`name`, `description`) VALUES
('科技', '科技前沿、技术动态'),
('财经', '金融市场、经济分析'),
('体育', '体育赛事、运动健康'),
('娱乐', '影视综艺、明星动态'),
('国际', '国际新闻、全球事务');

INSERT IGNORE INTO `articles` (`title`, `content`, `category_id`, `author`, `view_count`, `image_url`) VALUES
('OpenAI 发布 GPT-5，技术革命再进一步', '当地时间本周二，OpenAI 正式发布 GPT-5，这一版本在推理能力、多模态理解以及上下文窗口方面均有质的飞跃据悉，GPT-5 在多项基准测试中超越了人类专家水平，尤其在数学证明和代码生成任务上表现惊艳。OpenAI CEO 表示，GPT-5 将改变教育、医疗和法律等行业的工作方式。', 1, '张明', 12543, 'https://picsum.photos/seed/gpt5/800/400'),
('A股三大指数集体收涨，市场信心显著恢复', '今日A股市场表现强劲，沪指收涨 2.31%，深成指上涨 1.86%，创业板指涨 1.42%。北向资金大幅净流入超过 200 亿元，多个板块集体飘红。分析师指出，国内政策面持续释放暖意，加之经济数据企稳回升，市场做多情绪明显升温。', 2, '李华', 8721, 'https://picsum.photos/seed/stock/800/400'),
('中国女排3-0横扫日本队，世界杯夺冠', '在昨晚结束的女排世界杯焦点战中，中国女排以 3-0 的完美比分横扫日本队，成功夺得本届世界杯冠军。三局比分为 25-17、25-18、25-20。队长袁心玥砍下全场最高的 18 分，荣获 MVP。主教练赛后表示：队员们的拼搏精神和团队协作是取胜的关键。', 3, '王磊', 21356, 'https://picsum.photos/seed/volleyball/800/400'),
('《流浪地球3》定档春节，刘慈欣担任编剧', '备受期待的科幻巨制《流浪地球3》正式宣布定档2025年春节档，并发布首支预告片。导演郭帆透露，第三部将全面升级特效制作水准，故事将延续前两部的宏大叙事，同时加入全新角色和更加复杂的情感线索。原著作者刘慈欣亲自参与编剧工作。', 4, '陈雨', 6543, 'https://picsum.photos/seed/movie/800/400'),
('欧盟就碳中和达成新协议，2035年禁售燃油车', '欧盟委员会昨日宣布，各成员国已就2035年全面禁售燃油汽车达成最终协议，并同意设立 3000 亿欧元的绿色转型基金。此举被视为全球应对气候变化的重要里程碑，宝马、大众等欧洲车企随即发布声明表示支持，并加速推进电动化战略。', 5, '赵薇', 15892, 'https://picsum.photos/seed/eu/800/400');

SET FOREIGN_KEY_CHECKS = 1;
