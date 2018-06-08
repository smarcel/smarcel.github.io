// Created by iWeb 3.0.4 local-build-20180608

function createMediaStream_id1()
{return IWCreatePhotocast("http://sebastienmarcel.com/Test/Photos_files/rss.xml",true);}
function initializeMediaStream_id1()
{createMediaStream_id1().load('http://sebastienmarcel.com/Test',function(imageStream)
{var entryCount=imageStream.length;var headerView=widgets['widget1'];headerView.setPreferenceForKey(imageStream.length,'entryCount');NotificationCenter.postNotification(new IWNotification('SetPage','id1',{pageIndex:0}));});}
function layoutMediaGrid_id1(range)
{createMediaStream_id1().load('http://sebastienmarcel.com/Test',function(imageStream)
{if(range==null)
{range=new IWRange(0,imageStream.length);}
IWLayoutPhotoGrid('id1',new IWPhotoGridLayout(2,new IWSize(254,254),new IWSize(254,30),new IWSize(305,299),27,27,0,new IWSize(33,37)),new IWPhotoFrame([IWCreateImage('Photos_files/Freestyle_01.png'),IWCreateImage('Photos_files/Freestyle_02.png'),IWCreateImage('Photos_files/Freestyle_03.png'),IWCreateImage('Photos_files/Freestyle_06.png'),IWCreateImage('Photos_files/Freestyle_09.png'),IWCreateImage('Photos_files/Freestyle_08.png'),IWCreateImage('Photos_files/Freestyle_07.png'),IWCreateImage('Photos_files/Freestyle_04.png')],null,2,0.850000,3.000000,3.000000,3.000000,3.000000,22.000000,24.000000,23.000000,25.000000,166.000000,222.000000,166.000000,222.000000,null,null,null,0.100000),imageStream,range,null,null,1.000000,{backgroundColor:'rgb(0, 0, 0)',reflectionHeight:100,reflectionOffset:2,captionHeight:100,fullScreen:0,transitionIndex:2},'Media/slideshow.html','widget1','widget2','widget3')});}
function relayoutMediaGrid_id1(notification)
{var userInfo=notification.userInfo();var range=userInfo['range'];layoutMediaGrid_id1(range);}
function onStubPage()
{var args=window.location.href.toQueryParams();parent.IWMediaStreamPhotoPageSetMediaStream(createMediaStream_id1(),args.id);}
if(window.stubPage)
{onStubPage();}
setTransparentGifURL('Media/transparent.gif');function hostedOnDM()
{return false;}
function onPageLoad()
{IWRegisterNamedImage('comment overlay','Media/Photo-Overlay-Comment.png')
IWRegisterNamedImage('movie overlay','Media/Photo-Overlay-Movie.png')
loadMozillaCSS('Photos_files/PhotosMoz.css')
NotificationCenter.addObserver(null,relayoutMediaGrid_id1,'RangeChanged','id1')
fixAllIEPNGs('Media/transparent.gif');Widget.onload();initializeMediaStream_id1()
performPostEffectsFixups()}
function onPageUnload()
{Widget.onunload();}
