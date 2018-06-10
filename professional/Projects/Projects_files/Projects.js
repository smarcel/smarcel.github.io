// Created by iWeb 3.0.4 local-build-20180610

setTransparentGifURL('../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({stroke_3:new IWEmptyStroke(),stroke_1:new IWEmptyStroke(),stroke_0:new IWPhotoFrame([IWCreateImage('Projects_files/Formal_inset_01.png'),IWCreateImage('Projects_files/Formal_inset_02.png'),IWCreateImage('Projects_files/Formal_inset_03.png'),IWCreateImage('Projects_files/Formal_inset_06.png'),IWCreateImage('Projects_files/Formal_inset_09.png'),IWCreateImage('Projects_files/Formal_inset_08.png'),IWCreateImage('Projects_files/Formal_inset_07.png'),IWCreateImage('Projects_files/Formal_inset_04.png')],null,0,0.800000,1.000000,1.000000,1.000000,1.000000,14.000000,14.000000,14.000000,14.000000,191.000000,262.000000,191.000000,262.000000,null,null,null,0.100000),stroke_5:new IWEmptyStroke(),stroke_4:new IWEmptyStroke(),stroke_6:new IWEmptyStroke(),stroke_2:new IWEmptyStroke()});registry.applyEffects();}
function hostedOnDM()
{return false;}
function photocastSubscribe()
{photocastHelper("http://smarcel.ch/professional/Projects/rss.xml");}
function onPageLoad()
{loadMozillaCSS('Projects_files/ProjectsMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');detectBrowser();adjustLineHeightIfTooBig('id3');adjustFontSizeIfTooBig('id3');Widget.onload();fixAllIEPNGs('../Media/transparent.gif');fixupAllIEPNGBGs();applyEffects()}
function onPageUnload()
{Widget.onunload();}
