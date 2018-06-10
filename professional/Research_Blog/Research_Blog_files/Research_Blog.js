// Created by iWeb 3.0.4 local-build-20180610

setTransparentGifURL('../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({shadow_0:new IWShadow({blurRadius:10,offset:new IWPoint(4.2426,4.2426),color:'#000000',opacity:0.750000}),stroke_0:new IWPhotoFrame([IWCreateImage('Research_Blog_files/Pushpin_01.jpg'),IWCreateImage('Research_Blog_files/Pushpin_02.jpg'),IWCreateImage('Research_Blog_files/Pushpin_03.jpg'),IWCreateImage('Research_Blog_files/Pushpin_06.jpg'),IWCreateImage('Research_Blog_files/Pushpin_09.jpg'),IWCreateImage('Research_Blog_files/Pushpin_02_1.jpg'),IWCreateImage('Research_Blog_files/Pushpin_03_1.jpg'),IWCreateImage('Research_Blog_files/Pushpin_04.jpg')],null,1,0.407895,0.000000,0.000000,0.000000,0.000000,18.000000,18.000000,18.000000,18.000000,298.000000,472.000000,298.000000,472.000000,'Research_Blog_files/bullet_pp_3.png',new IWPoint(0.500000,-10),new IWSize(45,65),0.100000)});registry.applyEffects();}
function hostedOnDM()
{return false;}
function photocastSubscribe()
{photocastHelper("http://smarcel.ch/professional/Research_Blog/rss.xml");}
function onPageLoad()
{loadMozillaCSS('Research_Blog_files/Research_BlogMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');detectBrowser();adjustLineHeightIfTooBig('id3');adjustFontSizeIfTooBig('id3');Widget.onload();fixAllIEPNGs('../Media/transparent.gif');applyEffects()}
function onPageUnload()
{Widget.onunload();}
