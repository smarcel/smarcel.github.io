// Created by iWeb 3.0.4 local-build-20180609

function writeMovie1()
{detectBrowser();if(windowsInternetExplorer)
{document.write('<object id="id3" classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" codebase="http://www.apple.com/qtactivex/qtplugin.cab" width="311" height="249" style="height: 249px; left: 33px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="../../Media/hcigesture.mpg" /><param name="controller" value="true" /><param name="autoplay" value="false" /><param name="scale" value="tofit" /><param name="volume" value="100" /><param name="loop" value="false" /></object>');}
else if(isiPhone)
{document.write('<object id="id3" type="video/quicktime" width="311" height="249" style="height: 249px; left: 33px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="Gesture-based_Interface_files/hcigesture.jpg"/><param name="target" value="myself"/><param name="href" value="../../../Media/hcigesture.mpg"/><param name="controller" value="true"/><param name="scale" value="tofit"/></object>');}
else
{document.write('<object id="id3" type="video/quicktime" width="311" height="249" data="../../Media/hcigesture.mpg" style="height: 249px; left: 33px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="../../Media/hcigesture.mpg"/><param name="controller" value="true"/><param name="autoplay" value="false"/><param name="scale" value="tofit"/><param name="volume" value="100"/><param name="loop" value="false"/></object>');}}
function writeMovie2()
{detectBrowser();if(windowsInternetExplorer)
{document.write('<object id="id5" classid="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B" codebase="http://www.apple.com/qtactivex/qtplugin.cab" width="311" height="249" style="height: 249px; left: 358px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="../../Media/postures.mpg" /><param name="controller" value="true" /><param name="autoplay" value="false" /><param name="scale" value="tofit" /><param name="volume" value="100" /><param name="loop" value="false" /></object>');}
else if(isiPhone)
{document.write('<object id="id5" type="video/quicktime" width="311" height="249" style="height: 249px; left: 358px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="Gesture-based_Interface_files/postures.jpg"/><param name="target" value="myself"/><param name="href" value="../../../Media/postures.mpg"/><param name="controller" value="true"/><param name="scale" value="tofit"/></object>');}
else
{document.write('<object id="id5" type="video/quicktime" width="311" height="249" data="../../Media/postures.mpg" style="height: 249px; left: 358px; position: absolute; top: 51px; width: 311px; z-index: 1; "><param name="src" value="../../Media/postures.mpg"/><param name="controller" value="true"/><param name="autoplay" value="false"/><param name="scale" value="tofit"/><param name="volume" value="100"/><param name="loop" value="false"/></object>');}}
setTransparentGifURL('../../Media/transparent.gif');function applyEffects()
{var registry=IWCreateEffectRegistry();registry.registerEffects({stroke_0:new IWPhotoFrame([IWCreateImage('Gesture-based_Interface_files/Formal_inset_01.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_02.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_03.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_06.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_09.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_08.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_07.png'),IWCreateImage('Gesture-based_Interface_files/Formal_inset_04.png')],null,0,1.000000,1.000000,1.000000,1.000000,1.000000,14.000000,14.000000,14.000000,14.000000,191.000000,262.000000,191.000000,262.000000,null,null,null,0.100000)});registry.applyEffects();}
function hostedOnDM()
{return false;}
function onPageLoad()
{loadMozillaCSS('Gesture-based_Interface_files/Gesture-based_InterfaceMoz.css')
adjustLineHeightIfTooBig('id1');adjustFontSizeIfTooBig('id1');adjustLineHeightIfTooBig('id2');adjustFontSizeIfTooBig('id2');adjustLineHeightIfTooBig('id4');adjustFontSizeIfTooBig('id4');Widget.onload();fixAllIEPNGs('../../Media/transparent.gif');applyEffects()}
function onPageUnload()
{Widget.onunload();}
