; Шаблон для переименования Sitemap
$document_root = $_SERVER['DOCUMENT_ROOT'];

$old_name = $document_root . '/__OLD_SITEMAP__';
$new_name = $document_root . '/__NEW_SITEMAP__';

if (file_exists($old_name)) {
    if (rename($old_name, $new_name)) {
        echo "Файл успешно переименован в __NEW_SITEMAP__";
    } else {
        echo "Ошибка при переименовании файла";
    }
} else {
    echo "Файл __OLD_SITEMAP__ не найден";
}
