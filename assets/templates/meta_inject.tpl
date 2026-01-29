$rawMetaTag = '__META__';

$url = (isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? "https" : "http") . "://" . $_SERVER['HTTP_HOST'];
$metateg = trim($rawMetaTag);

function getWordPressThemeName($url) {
    if (!preg_match('~^https?://~', $url)) {
        $url = 'http://' . $url;
    }
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (compatible; Bot/1.0)');
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    $html = curl_exec($ch);
    if (curl_errno($ch)) {
        echo "Ошибка: " . curl_error($ch) . "\n\n";
        curl_close($ch);
        return null;
    }
    curl_close($ch);
    if (preg_match('~wp-content/themes/([^/]+)/~', $html, $matches)) {
        return $matches[1];
    } else {
        return "Тема не найдена или сайт не на WordPress.";
    }
}

$themeName = getWordPressThemeName($url);
if ($themeName && $themeName !== "Тема не найдена или сайт не на WordPress.") {
    echo "\nНазвание активной темы: " . $themeName . "\n";
} else {
    echo "Не удалось определить активную тему.\n";
    exit;
}

if (str_ends_with($themeName, '-child')) {
    $parentTheme = substr($themeName, 0, -6);
    $themeName = $parentTheme;
}

$filePath = "wp-content/themes/$themeName/header.php";
if (!file_exists($filePath)) {
    die("Файл header.php не найден в теме $themeName\n");
}

if (!is_writable($filePath)) {
    die("Файл $filePath недоступен для записи. Проверьте права доступа.\n");
}

@chmod($filePath, 0755);

$fileContents = file_get_contents($filePath);

$backupFile = "$filePath.bak";
@copy($filePath, $backupFile);

if (preg_match('/<head[^>]*>/i', $fileContents, $matches)) {
    $headTag = $matches[0];
    $updatedContents = str_replace($headTag, $headTag . "\n    " . $metateg, $fileContents);

    if (file_put_contents($filePath, $updatedContents)) {
        echo "Метатег успешно добавлен сразу после <head> в header.php";
    } else {
        die("Ошибка при записи в файл header.php");
    }
} else {
    die("Тег <head> не найден в файле header.php");
}
