
<!DOCTYPE html>
<html lang="en">
<head>

<base href="https://www.cityoffortmeade.org/" />
	<meta charset="utf-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">

	

 

	
	

	<title>Fort Meade</title>



	<meta name="keywords" content=""/>



	<meta name="description" content="Fort Meade"/>
	<meta name="robots" content="index, follow">
	
	


<link href="/revize/plugins/setup/css/revize.css" rel="stylesheet" type="text/css" />
<link rel="stylesheet" href="/revize/plugins/document_center/document_center_styles.css">
<script type="text/javascript" src="/revize/plugins/document_center/simple_accordian.js"></script><script type="text/javascript">

//----- Check href of all <a...> tags, if it matchs page url and immediate parent is <LI>,
//		append "active" to className of all ancestor <LI> tags until the parent of the <LI>
//		tag is not <UL> or the parent of the <UL> is not another <LI> tag.
var functionRef = function setClassActive()
{
	var e;
	try
	{
		var pattern = new RegExp("http[s]?://.*?/(.*)[?#]?","");
		var tags = document.getElementsByTagName("A");
		if (tags)
		{
			for (var i=0;i<tags.length;i++)
			{
				var el = tags[i];
				var resultsTag = el.href.match(pattern);
				var resultsPage = location.href.match(pattern);
				if (!resultsTag || !resultsPage) continue;
				if (resultsTag[1] != resultsPage[1]) continue;
	
				// go up li tree marking this and all parent class=active
				var li = el.parentNode;
				while (li && li.tagName == 'LI')
				{
					if (li.className != '') 
						li.className += ' ';
					li.className += 'active';
					var ul = li.parentNode;
					if (!ul || ul.tagName != 'UL') break;
					li = ul.parentNode;
				}
				//let's catch all links e.g. topnav, leftnav, quick links, etc
				//break;	//found url match, quit checking tags
			}
		}
	}
	catch (e) {}
}
//----- Activate topnavActive once page loads
if (typeof addEventListener != 'undefined') addEventListener('load', functionRef, false);	//standards browser
else if (typeof attachEvent != 'undefined') attachEvent("onload", functionRef);				//IE early versions
</script>



<script type="text/javascript">



</script>





    

	<link rel="stylesheet" href="_assets_/plugins/bootstrap/css/bootstrap.min.css">
	<link rel="stylesheet" href="_assets_/fonts/font-awesome/css/font-awesome.min.css">
	<link rel="stylesheet" href="_assets_/css/animate.min.css">
	<link rel="stylesheet" href="_assets_/css/layout.css">

	<link rel="shortcut icon" href="_assets_/images/favicon.ico">
	<link rel="apple-touch-icon" href="_assets_/images/touch-icon-iphone.png">
	<link rel="apple-touch-icon" sizes="72x72" href="_assets_/images/touch-icon-ipad.png">
	<link rel="apple-touch-icon" sizes="114x114" href="_assets_/images/touch-icon-iphone4.png">
	<link rel="apple-touch-icon" sizes="144x144" href="_assets_/images/touch-icon-ipad2.png">

	<!-- Respond.js for IE8 support of HTML5 elements and media queries -->
	<!--[if lt IE 9]>
	  <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
	<![endif]-->




</head>
<body id="freeform">




<script type="text/javascript">
if (typeof(RZ) == 'undefined') RZ = {};
if (!RZ.link) RZ.link = new Object();
RZ.pagetype = 'template'
RZ.baseurlprefix = ''
RZ.baseurlpath = ''
RZ.protocolRelativeRevizeBaseUrl='//cms2.revize.com'

RZ.pagetemplatename = 'alert_detail'
RZ.pagetemplateid = '31'
RZ.pagemodule = ''
RZ.pagemoduleid = ''
RZ.pagerecordid = '';

RZ.pageid = 'alert_detail';
RZ.pageparentid = '';
RZ.pagesectionid = '0';
RZ.pagesectionname = 'Home Page';
RZ.pagesectionlevel = '0';
RZ.pagesectionfolder = '';
RZ.pagesectionfilter = 'sectionid=0';
RZ.pagelinkfilter = 'linklevel=0 and linksectionid=0';
RZ.pagelinklevel = '0';
RZ.pagelinkid = '-1';
RZ.pageidfield = '';

RZ.isnewrecord = false;
RZ.editmodule = '';
RZ.editrecordid = '';
RZ.editrecordversion = '';
RZ.editversion = '';
RZ.editaction = '';

RZ.page_roles = ''
RZ.page_users = ''
RZ.page_key = 'alert_detail[]'
RZ.parent_key = ''
RZ.inherit_key = ''
RZ.workflowname = ''
RZ.permissions_options = 'warningsOFF'
RZ.permissions_module = 'webspace_page_permissions'
RZ.webspace = 'fortmeadefl'
RZ.webspacedesc = "";

RZ.featurespattern = '(EZ)';
null

RZ.webspacelinksurl = ''
RZ.webspacelinksurl = './webspace/links.html'
RZ.workflowlist = ''
RZ.revizeserverurl = 'https://cms2.revize.com/revize/fortmeadefl';

if (!RZ.nextseq) RZ.nextseq = {linknames:{},modules:{}};

RZ.webspace_config = new Object();
RZ.webspace_config.admin_email = "noreply@revize.com";
RZ.webspace_config.calendar_options = "max_events=4";
RZ.webspace_config.form_captcha = "yes";
RZ.webspace_config.form_server = "revizeserver";
RZ.webspace_config.form_technology = "jsp";
RZ.webspace_config.formwizard_ftp_password = "";
RZ.webspace_config.formwizard_ftp_port = "";
RZ.webspace_config.formwizard_ftp_server = "";
RZ.webspace_config.formwizard_ftp_user = "";
RZ.webspace_config.formwizard_setup = "yes";
RZ.webspace_config.formwizard_smtp_password = "xxx";
RZ.webspace_config.formwizard_smtp_server = "xxx";
RZ.webspace_config.formwizard_smtp_user = "xxx";
RZ.webspace_config.google_analytics = "";
RZ.webspace_config.home_pageid = "0";
RZ.webspace_config.home_sectionid = "0";
RZ.webspace_config.home_template = "home,index,sitemap";
RZ.webspace_config.icon_email = "<img src=\"/revize/images/email_icon_yellow.gif\" width=\"16\" border=\"0\" height=\"17\" title=\"Request email notification when page changes\" alt=\"Request email notification when page changes\" style=\"\" />";
RZ.webspace_config.image_maxheight = "3000";
RZ.webspace_config.image_maxwidth = "3000";
RZ.webspace_config.image_setup = "yes";
RZ.webspace_config.livesite_url = "";
RZ.webspace_config.menu_links_module = "links";
RZ.webspace_config.menu_newsection = "";
RZ.webspace_config.menu_nexturl = "webspace_menu-editform.jsp";
RZ.webspace_config.menu_sections_module = "sections";
RZ.webspace_config.menu_system = "custom";
RZ.webspace_config.menu_version = "1.00";
RZ.webspace_config.new_menu_manager_enabled = "yes";
RZ.webspace_config.notify_return_url = "enotify/index.php";
RZ.webspace_config.rte_setup = "yes";
RZ.webspace_config.to_email = "webpageupdate_subscribers@revize.com";
RZ.webspace_config.use_folders = "1";

RZ.isauthenticationactive = true
RZ.warning = ""
RZ.adminwinmsg = null

RZ.channels = 'revize,Production';
RZ.jsversion = 1.2</script>
<script type="text/javascript" src="/revize/util/snippet_helper.js"></script>


 


<a href="#main" id="skip" class="btn" tabindex="0">Skip to main content</a>
<header>
	<div id="toggles" class="hidden-lg hidden-md">
		<div id="search-toggle" class="fa fa-search"></div>
		<div id="nav-toggle" class="fa fa-bars"></div>
	</div><!--/#toggles.hidden-lg.hidden-md-->
	<a href="./" id="logo">
		<img src="_assets_/images/logo.png" alt="navigation logo">
	</a>
	<div id="search">
		<form class="search-form" method="get" action="search.php">
			<input name="q" class="form-control search-input" placeholder="search" type="search" id="search-input">
			<button class="fa fa-search"></button>
		</form>
	</div><!-- /#search -->
	<nav>
			  <!-- start plugin: menus.topnav-onpage -->

	  <div class="float_button_anchor">
	     
<ul id="nav" class="v2_05-23-2012">
	<li class="menuLI level0 menuDisplay li-1"><a class="menuA level0 menuDisplay" href="index.php" target="_self">Home</a></li>
	<li class="menuLI level0 menuDisplay li-5 children"><a class="menuA level0 menuDisplay" href="departments/index.php" target="_self">Departments</a>
		<ul class="menuUL level1 menuHidden ul-58">
			<li class="menuLI level1 menuHidden li-58"><a class="menuA level1 menuHidden" href="departments/city_commssion.php" target="_self">City Commission</a></li>
			<li class="menuLI level1 menuHidden li-20 children"><a class="menuA level1 menuHidden" href="departments/administration.php" target="_self">Administration</a>
				<ul class="menuUL level2 menuHidden ul-124">
					<li class="menuLI level2 menuHidden li-124"><a class="menuA level2 menuHidden" href="departments/city_manager.php" target="_self">City Manager</a></li>
					<li class="menuLI level2 menuHidden li-205"><a class="menuA level2 menuHidden" href="departments/deputy_city_clerk/index.php" target="_self">Deputy City Clerk</a></li>
					<li class="menuLI level2 menuHidden li-126"><a class="menuA level2 menuHidden" href="departments/human_resources.php" target="_self">Human Resources</a></li>
					<li class="menuLI level2 menuHidden li-599"><a class="menuA level2 menuHidden" href="departments/assistant_city_manager.php" target="_self">Assistant City Manager</a></li>
					<li class="menuLI level2 menuHidden li-1248"><a class="menuA level2 menuHidden" href="departments/administrative_rule_book/index.php" target="_self">Administrative Rules</a></li>
					<li class="menuLI level2 menuHidden li-1360"><a class="menuA level2 menuHidden" href="index.php" target="_self">City Press Releases</a></li>
				</ul>
			</li>
			<li class="menuLI level1 menuHidden li-21"><a class="menuA level1 menuHidden" href="departments/building.php" target="_self">Building</a></li>
			<li class="menuLI level1 menuHidden li-304"><a class="menuA level1 menuHidden" href="departments/public_work.php" target="_self">Public Works</a></li>
			<li class="menuLI level1 menuHidden li-191"><a class="menuA level1 menuHidden" href="departments/code_enforcement.php" target="_self">Code Enforcement</a></li>
			<li class="menuLI level1 menuHidden li-23 children"><a class="menuA level1 menuHidden" href="departments/community_development.php" target="_self">Community Development -Planning and Zoning</a>
				<ul class="menuUL level2 menuHidden ul-277">
					<li class="menuLI level2 menuHidden li-277"><a class="menuA level2 menuHidden" href="departments/doing_business_with_fort_meade.php" target="_self">Doing Business with Fort Meade</a></li>
					<li class="menuLI level2 menuHidden li-60"><a class="menuA level2 menuHidden" href="departments/boards___commission.php" target="_self">Boards & Commission</a></li>
					<li class="menuLI level2 menuHidden li-27"><a class="menuA level2 menuHidden" href="departments/community_redevelopment_agency.php" target="_self">Community Redevelopment Agency</a></li>
					<li class="menuLI level2 menuHidden li-282"><a class="menuA level2 menuHidden" href="departments/planning.php" target="_self">Planning</a></li>
				</ul>
			</li>
			<li class="menuLI level1 menuHidden li-32"><a class="menuA level1 menuHidden" href="departments/recreation.php" target="_self">Community Center</a></li>
			<li class="menuLI level1 menuHidden li-24"><a class="menuA level1 menuHidden" href="departments/utility_billing_customer_service.php" target="_self">Customer Service</a></li>
			<li class="menuLI level1 menuHidden li-28"><a class="menuA level1 menuHidden" href="departments/finance.php" target="_self">Finance</a></li>
			<li class="menuLI level1 menuHidden li-204"><a class="menuA level1 menuHidden" href="departments/electric.php" target="_self">Electric</a></li>
			<li class="menuLI level1 menuHidden li-33"><a class="menuA level1 menuHidden" href="departments/fire.php" target="_self">Fire</a></li>
			<li class="menuLI level1 menuHidden li-34"><a class="menuA level1 menuHidden" href="departments/library.php" target="_self">Library</a></li>
			<li class="menuLI level1 menuHidden li-35"><a class="menuA level1 menuHidden" href="departments/police_(sheriff).php" target="_self">Police (Sheriff)</a></li>
			<li class="menuLI level1 menuHidden li-213"><a class="menuA level1 menuHidden" href="departments/streets.php" target="_self">Streets/Stormwater</a></li>
			<li class="menuLI level1 menuHidden li-214"><a class="menuA level1 menuHidden" href="departments/parks.php" target="_self">Parks</a></li>
			<li class="menuLI level1 menuHidden li-215"><a class="menuA level1 menuHidden" href="departments/water_wastewater.php" target="_self">Water/Wastewater</a></li>
			<li class="menuLI level1 menuHidden li-38"><a class="menuA level1 menuHidden" href="departments/faq.php" target="_self">FAQ</a></li>
		</ul>
	</li>
	<li class="menuLI level0 menuDisplay li-6 children"><a class="menuA level0 menuDisplay" href="residents/index.php" target="_self">Residents</a>
		<ul class="menuUL level1 menuHidden ul-39">
			<li class="menuLI level1 menuHidden li-39"><a class="menuA level1 menuHidden" href="residents/important_phone_numbers.php" target="_self">Important Phone Numbers</a></li>
			<li class="menuLI level1 menuHidden li-40"><a class="menuA level1 menuHidden" href="residents/utility_billing.php" target="_self">Utility Billing</a></li>
			<li class="menuLI level1 menuHidden li-41"><a class="menuA level1 menuHidden" href="residents/solid_waste.php" target="_self">Solid Waste</a></li>
			<li class="menuLI level1 menuHidden li-43"><a class="menuA level1 menuHidden" href="residents/water_conservation_best_pratice.php" target="_self">Water Conservation Best Pratice</a></li>
			<li class="menuLI level1 menuHidden li-61"><a class="menuA level1 menuHidden" href="residents/hurricane_info.php" target="_self">Hurricane Info</a></li>
			<li class="menuLI level1 menuHidden li-133"><a class="menuA level1 menuHidden" href="residents/living_in_fort_meade.php" target="_self">Living in Fort Meade</a></li>
			<li class="menuLI level1 menuHidden li-330"><a class="menuA level1 menuHidden" href="residents/2020_census.php" target="_self">2020 Census</a></li>
			<li class="menuLI level1 menuHidden li-1174"><a class="menuA level1 menuHidden" href="residents/curbside_clean_up.php" target="_self">Curbside Clean Up</a></li>
			<li class="menuLI level1 menuHidden li-1179"><a class="menuA level1 menuHidden" href="residents/pavilion_rentals_at_fort_meade_municipal_parks.php" target="_self">Pavilion Rentals at Fort Meade Municipal Parks</a></li>
		</ul>
	</li>
	<li class="menuLI level0 menuDisplay li-14 children"><a class="menuA level0 menuDisplay" href="visitors/job_openings.php" target="_self">Visitors</a>
		<ul class="menuUL level1 menuHidden ul-48">
			<li class="menuLI level1 menuHidden li-48"><a class="menuA level1 menuHidden" href="https://www.streamsongresort.com/" target="_new">STREAMSONG</a></li>
			<li class="menuLI level1 menuHidden li-51"><a class="menuA level1 menuHidden" href="https://fortmeadeflmuseum.com" target="_new">Fort Meade Historical Museum</a></li>
			<li class="menuLI level1 menuHidden li-202"><a class="menuA level1 menuHidden" href="https://ftmeadechamber.com/" target="_new">Fort Meade Chamber of Commerce</a></li>
			<li class="menuLI level1 menuHidden li-1165"><a class="menuA level1 menuHidden" href="departments/human_resources.php" target="_self">Job Opportunities</a></li>
		</ul>
	</li>
</ul>

	  </div>
	  <!-- end plugin: menus.topnav-onpage -->
	</nav>
</header>

<div id="slider">
	
	
	<div class="sliderbtn">
        
        
        
        <script language="JavaScript" type="text/JavaScript">
            RZ.module = 'slider';
            RZ.nexturl = "editforms/slider-editlist.jsp?pageid=alert_detail";
            RZ.popupwidth = ''; RZ.popupheight = ''; RZ.popupscroll = '';
            RZ.img = '<span class="rzBtn">Edit This List</span>';
            RZ.caption = '';
            RZ.options = '';
            if (typeof RZaction != 'undefined') RZaction('editlist');
        </script>
        
    </div><!-- /.sliderbtn -->
    




<script language="JavaScript" type="text/JavaScript">
if (typeof RZlistbegin != 'undefined') RZlistbegin(2)
</script>

	
        
            
            
        
    
<script language="JavaScript" type="text/JavaScript">
if (typeof RZlinktemplate != 'undefined') RZlinktemplate('slider','','')
if (typeof RZ.nextseq != 'undefined') RZ.nextseq.modules['slider_2']={field:'seq_no',seq:'1.00'};
</script>


<ul class="bxslider">
	<li style="background:url('_assets_/images/slide-1.jpg') center no-repeat;background-size:cover;"></li>
</ul><!-- /.bxslider -->
</div><!--/#slider-->
<main tabindex="-1" id="main">
	<div class="clearfix">
		<div id="flyout-background" class="hidden-sm hidden-xs"></div>
<aside id="flyout-wrap">
        <div class="header-editbtn">
                  <script language="JavaScript" type="text/JavaScript">
                                RZ.module = 'global';
                                RZ.nexturl = 'editforms/header-editform.jsp';
                                RZ.img = '<span class="rzBtn">Edit Header</span>';
                                RZ.set = 'global.pageid=flyout';
                                RZ.options = '';
                                if (typeof RZaction != 'undefined') RZaction('editform');
                            </script>
                        </div><!-- /.header-editbtn -->
                        
			<h1 id="flyout-header">Contacts and Links</h1>
						  <!-- start plugin: menus.leftnav-section -->
			  
			  


			  
			  
			  <script language="JavaScript" type="text/JavaScript">
			  RZ.module = 'links';
			  RZ.nexturl = "/revize/plugins/menus/webspace_menu-editlist.jsp?pageid=alert_detail&"
			           + "linksfilter=linkplacement=leftnav and linkparentid=0&"
			           + "numberoflevels=2&"
			           + "linkoptions=url,template,file&"
			           + "linknewsection=*all*";
			  RZ.img = '<span class="rzBtn">Edit This List</span>';
			  RZ.caption = '';
			  RZ.set = "links.linkplacement=leftnav"
			  RZ.options = '';
			  if (typeof RZaction != 'undefined') RZaction('editlist');
			  </script>
			  
			  
 <ul  id="flyout" class="v08-30-2012">
</ul>

			  <!-- end plugin: menus.leftnav-section -->
		</aside><!--/#flyout-wrap-->
		<article id="entry">
			<div id="breadcrumbs">

<a href="./">Home</a> Alert Detail
</div><!-- /#breadcrumbs -->
			<h2 id="page-title">

  


Alerts
</h2>
			<div class="centerBtns">
	
          
          <script language="JavaScript" type="text/JavaScript">
            RZ.module = 'alert';
            RZ.recordid = '';
            RZ.nexturl = "editforms/alert-editform.jsp";
            RZ.img = '<span class="rzBtn">Edit Alert Content</span>';
            RZ.set = 'alert.pageid=alert';
            RZ.options = '';
            if (typeof RZaction != 'undefined') RZaction('editform');
          </script>
     
    
		<script language="JavaScript" type="text/JavaScript">
            RZ.module = 'freeform';
            RZ.recordid = '';
            RZ.nexturl = "editforms/metadata-editform.jsp";
            RZ.popupwidth = ''; RZ.popupheight = ''; RZ.popupscroll = '';
            RZ.img = '<span class="rzBtn">Edit Metadata</span>';
            RZ.set = "freeform.pageid=alert_detail";
            RZ.options = '';
            if (typeof RZaction != 'undefined') RZaction('editform');
        </script>
    
    
        
        
        <script language="JavaScript" type="text/JavaScript">
            RZ.nexturl = '';
            RZ.img = '<img src="images/edit/permissions.jpg" alt="Permissions" border="0" />';
            RZ.options = '';
            if (typeof RZaction != 'undefined') RZaction('permissions');
        </script>
    
</div><!-- /.centerBtns -->



    Emergency dial <strong>911<br /></strong>Non-emergency police matters <a href="tel:8632986200">863-298-6200</a><br /><strong>Office Hours 8:00 am - 5:00 pm</strong><br />Customer Service <a href="tel:8632851100">285-1100</a><br />Code Enforcement <a href="tel:8632265325">863-226-5325</a><br /><strong>After Hours Emergencies</strong><br />Electric <a href="tel:8553483056">855-348-3056</a><br />Water/Sewer <a href="tel:8632268472">863-226-8472</a><br />Streets/Stormwater <a href="tel:8553483056">855-348-3056</a>
  
<div id="post">
    
</div><!-- /#post -->
		</article><!--/#entry-->
	</div><!--/.clearfix-->
	<section id="bottom-links">
		<div class="container">
			<div class="row">
				<div class="col-md-3 bottom-links-divider">
					
                    
                    <h4 class="bottom-links-header">City Commission</h4>
                    
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlistbegin != 'undefined') RZlistbegin(7)
</script>

						
                        
                    
                                  
                                
                    <a href="departments/city_commssion.php" target="_self" class="bottom-link">Commissioners</a>
                    
                        
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlinktemplate != 'undefined') RZlinktemplate('links','','innerlinks')
if (typeof RZ.nextseq != 'undefined') RZ.nextseq.linknames['innerlinks']={field:'linkseq',seq:'2.00'};
</script>

				</div><!--/.col-md-3.bottom-links-divider-->
				<div class="col-md-3 bottom-links-divider">
					
                    
                    <h4 class="bottom-links-header">departments</h4>
                    
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlistbegin != 'undefined') RZlistbegin(8)
</script>

						
                        
                    
                                  
                                
                    <a href="departments/city_manager.php" target="_self" class="bottom-link">City Manager</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/deputy_city_clerk/index.php" target="_self" class="bottom-link">Deputy City Clerk</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/human_resources.php" target="_self" class="bottom-link">Human Resources</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/finance.php" target="_self" class="bottom-link">Finance</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/utility_billing_customer_service.php" target="_self" class="bottom-link">Customer Service</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/fire.php" target="_self" class="bottom-link">Fire</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/recreation.php" target="_self" class="bottom-link">Community Center</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/building.php" target="_self" class="bottom-link">Building</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/city_mobile_home_park.php" target="_self" class="bottom-link">City Mobile Home Park</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/code_enforcement.php" target="_self" class="bottom-link">Code Enforcement</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/library.php" target="_self" class="bottom-link">Library</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/electric.php" target="_self" class="bottom-link">Electric</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/streets.php" target="_self" class="bottom-link">Streets</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/water_wastewater.php" target="_self" class="bottom-link">Water/Wastewater</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/parks.php" target="_self" class="bottom-link">Parks</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/public_work.php" target="_self" class="bottom-link">Public Works</a>
                    
                        
                        
                    
                                  
                                
                    <a href="departments/planning.php" target="_self" class="bottom-link">Planning and Zoning</a>
                    
                        
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlinktemplate != 'undefined') RZlinktemplate('links','','innerlinks')
if (typeof RZ.nextseq != 'undefined') RZ.nextseq.linknames['innerlinks']={field:'linkseq',seq:'18.00'};
</script>

				</div><!--/.col-md-3.bottom-links-divider-->
				<div class="col-md-3 bottom-links-divider">
                
                    
                    <h4 class="bottom-links-header">Accessibility Statements</h4>
                    
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlistbegin != 'undefined') RZlistbegin(9)
</script>

						
                        
                    
                                  
                                
                    <a href="resources_link/index.php" target="_self" class="bottom-link">Accessibility</a>
                    
                        
                        
                    
                                  
                                
                    <a href="fair_housing/fair_housing.php" target="_self" class="bottom-link">Fair Housing</a>
                    
                        
                        
                    
                                  
                                
                    <a href="equal_employment_opportunity/equal_employment_opportunity.php" target="_self" class="bottom-link">Equal Employment Opportunity</a>
                    
                        
                        
                    
                                  
                                
                    <a href="ada_compliance/index.php" target="_self" class="bottom-link">ADA Compliance</a>
                    
                        
                    <script language="JavaScript" type="text/JavaScript">
if (typeof RZlinktemplate != 'undefined') RZlinktemplate('links','','innerlinks')
if (typeof RZ.nextseq != 'undefined') RZ.nextseq.linknames['innerlinks']={field:'linkseq',seq:'5.00'};
</script>

				</div><!--/.col-md-3.bottom-links-divider-->
				<div class="col-md-3 bottom-links-divider">
                
                    
					<h4 id="address-header">contact us</h4>
                    
					<div id="address">
                    	
8 West Broadway Street <br>
                        
863.285.1100
					</div><!--/#address-->
				</div><!--/.col-md-3.bottom-links-divider-->
			</div><!--/.row-->
		</div><!--/.container-->
	</section><!--/#bottom-links-->
</main>
<footer>
	<div class="container">
		<div class="row">
        
            
			<div class="col-md-6" id="footer-text">	
            	&copy; 2026
			</div><!--/.col-md-6#footer-text-->
			<div class="col-md-6 text-right" id="revize">
				Powered by <a href="./" id="revize-link">Revize</a>, The Government Website Experts &nbsp;| &nbsp;
               
                <a href="https://cms2.revize.com/revize/security/index.jsp?webspace=fortmeadefl&filename=/alert_detail.php" id="revize-login">Login</a>
			</div><!--/.col-md-6.text-right#revize-->
		</div><!--/.row-->
	</div><!--/.container-->
</footer>





<!-- Share widget make into an include file -->
<button type="button" class="share-btn floating-share-btn" data-toggle="modal" data-target="#shareModal">
	<i class="fa fa-share-alt"></i>
	<span>SHARE</span>
</button>

<div class="modal fade" id="shareModal" tabindex="-1" role="dialog" aria-labelledby="shareModal">
	<div class="modal-dialog modal-lg" role="document">
		<div class="modal-content">
			<div class="modal-header">
				<button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
				<h4 class="modal-title" id="myModalLabel">Share this page</h4>
			</div>
			<div class="modal-body">
				<div class="copylink">
					<p>Copy and paste this code into your website.</p>
					<pre>&lt;a href="http://www.cityoffortmeade.org/alert_detail.php">Your Link Name&lt;/a&gt;</pre>
				</div><!-- /.copylink -->
				<div class="share-btns">
					<p>Share this page on your favorite Social network</p>
					<div class="row">
						<div class="col-md-3 col-xs-6">
							<a href="https://www.facebook.com/sharer/sharer.php?u=http://www.cityoffortmeade.org/alert_detail.php" class="btn-facebook" onclick="return !window.open(this.href, 'facebook ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-facebook"></i> Facebook
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.twitter.com/home?status=http://www.cityoffortmeade.org/alert_detail.php" class="btn-twitter" onclick="return !window.open(this.href, 'twitter ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-twitter"></i> Twitter
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.plus.google.com/share?url=http://www.cityoffortmeade.org/alert_detail.php" class="btn-google" onclick="return !window.open(this.href, 'google ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-google-plus"></i> Google Plus
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.reddit.com/submit?url=http://www.cityoffortmeade.org/alert_detail.php" class="btn-reddit" onclick="return !window.open(this.href, 'redit ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-reddit"></i> Reddit
							</a>
						</div>
					</div><!-- /.row -->
				</div><!-- /.share-btns -->
				<button type="button" class="btn btn-success btn-lg" data-dismiss="modal">Close</button>
			</div><!-- /.modal-body -->
		</div>
	</div><!-- /.modal-dialog -->
</div><!-- /.modal -->
<!-- Share widget make into an include file -->

	<script src="_assets_/js/jquery.min.js"></script>
	<script src="_assets_/plugins/modernizr/modernizr.custom.js"></script>
    <script src="_assets_/plugins/jquery.bxslider/jquery.bxslider.min.js"></script>
    <script src="_assets_/plugins/bootstrap/js/bootstrap.min.js"></script>
    <script src="_assets_/js/scripts.js"></script>






</body>
</html>
