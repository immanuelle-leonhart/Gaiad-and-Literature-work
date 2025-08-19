<?php
if ( !defined( 'MEDIAWIKI' ) ) {
    exit( 1 );
}
$wgSitename = 'wikibase-docker';
$wgMetaNamespace = 'Project';
$wgServer = 'http://localhost:8080';
$wgScriptPath = '';
$wgUsePathInfo = true;
$wgArticlePath = '/wiki/$1';
$wgScriptExtension = '.php';
$wgResourceBasePath = $wgScriptPath;
$wgLogos = [ '1x' => $wgResourceBasePath . '/resources/assets/wiki.png' ];
$wgEmergencyContact = 'apache@localhost';
$wgPasswordSender = 'apache@localhost';
$wgEnotifUserTalk = false;
$wgEnotifWatchlist = false;
$wgEmailAuthentication = true;
$wgDBtype = 'mysql';
$wgDBserver = 'mysql.svc:3306';
$wgDBname = 'mediawiki';
$wgDBuser = 'mediawiki';
$wgDBpassword = 'password';
$wgDBmysql5 = false;
$wgMainCacheType = CACHE_ACCEL;
$wgMemCachedServers = [];
$wgEnableUploads = false;
$wgUseImageMagick = true;
$wgImageMagickConvertCommand = '/usr/bin/convert';
$wgShellLocale = 'C.UTF-8';
$wgLanguageCode = 'en';
$wgSecretKey = 'secretkey';
$wgAuthenticationTokenVersion = '1';
$wgUpgradeKey = 'upgradekey';
$wgDefaultSkin = 'vector';
wfLoadSkin( 'Vector' );
wfLoadExtension( 'WikiEditor' );

# Wikibase Configuration
$wgEnableWikibaseRepo = true;
$wgEnableWikibaseClient = false;
require_once "$IP/extensions/Wikibase/repo/Wikibase.php";
require_once "$IP/extensions/Wikibase/repo/ExampleSettings.php";
$wgWBRepoSettings['allowEntityImport'] = true;

$wgGroupPermissions['*']['createaccount'] = true;
$wgGroupPermissions['*']['edit'] = true;
$wgGroupPermissions['*']['read'] = true;