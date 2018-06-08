// Created by iWeb 3.0.4 local-build-20180608

setTransparentGifURL('../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({shadow_0:new IWShadow({blurRadius:1,offset:new IWPoint(1.4142,1.4142),color:'#000000',opacity:0.440000})});registry.applyEffects();}
function hostedOnDM()
{return false;}
function photocastSubscribe()
{photocastHelper("http://sebastienmarcel.com/Test/Blog/rss.xml");}
function onPageLoad()
{loadMozillaCSS('Blog_files/BlogMoz.css')
detectBrowser();fixAllIEPNGs('../Media/transparent.gif');Widget.onload();fixupAllIEPNGBGs();IMpreload('Blog_files','shapeimage_6','0');applyEffects()}
function onPageUnload()
{Widget.onunload();}
