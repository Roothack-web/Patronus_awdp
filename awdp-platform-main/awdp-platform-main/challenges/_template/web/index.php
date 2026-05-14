<?php
// ============================================================
// AWDP Challenge Template — Vulnerable Web App
// ============================================================
// This is your challenge entry point. Create a vulnerability
// (SQLi, SSTI, LFI, RCE, SSRF, etc.) that participants must
// exploit to get the flag.
//
// Dynamic flag: read from /flag file (written by start.sh)
// Static flag:  defined in admin panel, submitted directly
// ============================================================

$flag = trim(file_get_contents('/flag'));

// --- Your vulnerable code here ---

// Example: SQL injection
// $id = $_GET['id'] ?? '';
// $mysqli = new mysqli('localhost', 'user', 'pass', 'db');
// $result = $mysqli->query("SELECT * FROM articles WHERE id = $id");

?>
<!DOCTYPE html>
<html>
<head>
    <title>Challenge</title>
    <meta charset="utf-8">
</head>
<body>
    <h1>Challenge Template</h1>
    <p>Replace this with your challenge.</p>
    <!-- Flag location hint (if needed): /flag -->
</body>
</html>
