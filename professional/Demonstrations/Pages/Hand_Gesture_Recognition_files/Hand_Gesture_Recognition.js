// Created by iWeb 3.0.4 local-build-20180609

function writeMovie1()
{detectBrowser();if(windowsInternetExplorer)
{document.write('<object id="id3" classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" codebase="http://www.apple.com/qtactivex/qtplugin.cab" width="475" height="194" style="height: 194px; left: 112px; position: absolute; top: 47px; width: 475px; z-index: 1; "><param name="src" value="../../Media/gestures.mpg" /><param name="controller" value="true" /><param name="autoplay" value="false" /><param name="scale" value="tofit" /><param name="volume" value="100" /><param name="loop" value="false" /></object>');}
else if(isiPhone)
{document.write('<object id="id3" type="video/quicktime" width="475" height="194" style="height: 194px; left: 112px; position: absolute; top: 47px; width: 475px; z-index: 1; "><param name="src" value="Hand_Gesture_Recognition_files/gestures.jpg"/><param name="target" value="myself"/><param name="href" value="../../../Media/gestures.mpg"/><param name="controller" value="true"/><param name="scale" value="tofit"/></object>');}
else
{document.write('<object id="id3" type="video/quicktime" width="475" height="194" data="../../Media/gestures.mpg" style="height: 194px; left: 112px; position: absolute; top: 47px; width: 475px; z-index: 1; "><param name="src" value="../../Media/gestures.mpg"/><param name="controller" value="true"/><param name="autoplay" value="false"/><param name="scale" value="tofit"/><param name="volume" value="100"/><param name="loop" value="false"/></object>');}}
setTransparentGifURL('../../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({stroke_0:new IWPhotoFrame([IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_01.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_02.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_03.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_06.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_09.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_08.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_07.png'),IWCreateImage('Hand_Gesture_Recognition_files/Formal_inset_04.png')],null,0,1.000000,1.000000,1.000000,1.000000,1.000000,14.000000,14.000000,14.000000,14.000000,191.000000,262.000000,191.000000,262.000000,null,null,null,0.100000)});registry.applyEffects();}
function hostedOnDM()
{return false;}
function onPageLoad()
{loadMozillaCSS('Hand_Gesture_Recognition_files/Hand_Gesture_RecognitionMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');adjustLineHeightIfTooBig('id4');adjustFontSizeIfTooBig('id4');Widget.onload();fixAllIEPNGs('../../Media/transparent.gif');applyEffects()}
function onPageUnload()
{Widget.onunload();}
