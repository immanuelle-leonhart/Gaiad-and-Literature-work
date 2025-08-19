<?php
if ( !defined( "MEDIAWIKI" ) ) { exit; }
$wgSitename = "Local Evolutionism";
$wgServer = "http://localhost:8080";
$wgScriptPath = "";
$wgDBtype = "mysql";
$wgDBserver = "db";
$wgDBname = "mediawiki";
$wgDBuser = "mediawiki";
$wgDBpassword = "password";
$wgSecretKey = "local_secret_key_for_testing";
$wgLanguageCode = "en";
$wgDefaultSkin = "vector";
wfLoadSkin( "Vector" );
$wgGroupPermissions["*"]["createaccount"] = false;
$wgGroupPermissions["*"]["edit"] = false;
$wgShowExceptionDetails = true;
