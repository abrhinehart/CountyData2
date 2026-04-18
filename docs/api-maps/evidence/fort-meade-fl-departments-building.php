
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
RZ.baseurlprefix = '../'
RZ.baseurlpath = 'departments/'
RZ.protocolRelativeRevizeBaseUrl='//cms2.revize.com'

RZ.pagetemplatename = 'freeform'
RZ.pagetemplateid = '0'
RZ.pagemodule = 'links'
RZ.pagemoduleid = '1'
RZ.pagerecordid = '21';

RZ.pageid = 'links-21';
RZ.pageparentid = '5';
RZ.pagesectionid = '5';
RZ.pagesectionname = 'departments';
RZ.pagesectionlevel = '1';
RZ.pagesectionfolder = 'departments/';
RZ.pagesectionfilter = 'sectionid=5';
RZ.pagelinkfilter = 'linklevel=1 and linksectionid=5';
RZ.pagelinklevel = '1';
RZ.pagelinkid = '21';
RZ.pageidfield = '';

RZ.isnewrecord = false;
RZ.editmodule = '';
RZ.editrecordid = '21';
RZ.editrecordversion = '';
RZ.editversion = '';
RZ.editaction = '';

RZ.page_roles = ''
RZ.page_users = 'f767b2e822595ebbb1e61ff207de977eda46da8b8c03cba81cf0521e54794747|1968426d560270178d9e46891198d492d9ffda6455d5bfcd82c692ea06d6a364'
RZ.page_key = 'freeform[21]'
RZ.parent_key = 'freeform[5]'
RZ.inherit_key = 'index[]'
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


 


<a href="departments/building.php#main" id="skip" class="btn" tabindex="0">Skip to main content</a>
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
	<li class="menuLI level0 menuSelectedParent first li-5 children"><a class="menuA level0 menuSelectedParent first" href="departments/index.php" target="_self">Departments</a>
		<ul class="menuUL level1 menuSelectedUncle first ul-58">
			<li class="menuLI level1 menuSelectedUncle first li-58"><a class="menuA level1 menuSelectedUncle first" href="departments/city_commssion.php" target="_self">City Commission</a></li>
			<li class="menuLI level1 menuSelectedUncle li-20 children"><a class="menuA level1 menuSelectedUncle" href="departments/administration.php" target="_self">Administration</a>
				<ul class="menuUL level2 menuHidden ul-124">
					<li class="menuLI level2 menuHidden li-124"><a class="menuA level2 menuHidden" href="departments/city_manager.php" target="_self">City Manager</a></li>
					<li class="menuLI level2 menuHidden li-205"><a class="menuA level2 menuHidden" href="departments/deputy_city_clerk/index.php" target="_self">Deputy City Clerk</a></li>
					<li class="menuLI level2 menuHidden li-126"><a class="menuA level2 menuHidden" href="departments/human_resources.php" target="_self">Human Resources</a></li>
					<li class="menuLI level2 menuHidden li-599"><a class="menuA level2 menuHidden" href="departments/assistant_city_manager.php" target="_self">Assistant City Manager</a></li>
					<li class="menuLI level2 menuHidden li-1248"><a class="menuA level2 menuHidden" href="departments/administrative_rule_book/index.php" target="_self">Administrative Rules</a></li>
					<li class="menuLI level2 menuHidden li-1360"><a class="menuA level2 menuHidden" href="index.php" target="_self">City Press Releases</a></li>
				</ul>
			</li>
			<li class="menuLI level1 menuSelectedItem li-21"><a class="menuA level1 menuSelectedItem" href="departments/building.php" target="_self">Building</a></li>
			<li class="menuLI level1 menuSelectedUncle li-304"><a class="menuA level1 menuSelectedUncle" href="departments/public_work.php" target="_self">Public Works</a></li>
			<li class="menuLI level1 menuSelectedUncle li-191"><a class="menuA level1 menuSelectedUncle" href="departments/code_enforcement.php" target="_self">Code Enforcement</a></li>
			<li class="menuLI level1 menuSelectedUncle li-23 children"><a class="menuA level1 menuSelectedUncle" href="departments/community_development.php" target="_self">Community Development -Planning and Zoning</a>
				<ul class="menuUL level2 menuHidden ul-277">
					<li class="menuLI level2 menuHidden li-277"><a class="menuA level2 menuHidden" href="departments/doing_business_with_fort_meade.php" target="_self">Doing Business with Fort Meade</a></li>
					<li class="menuLI level2 menuHidden li-60"><a class="menuA level2 menuHidden" href="departments/boards___commission.php" target="_self">Boards & Commission</a></li>
					<li class="menuLI level2 menuHidden li-27"><a class="menuA level2 menuHidden" href="departments/community_redevelopment_agency.php" target="_self">Community Redevelopment Agency</a></li>
					<li class="menuLI level2 menuHidden li-282"><a class="menuA level2 menuHidden" href="departments/planning.php" target="_self">Planning</a></li>
				</ul>
			</li>
			<li class="menuLI level1 menuSelectedUncle li-32"><a class="menuA level1 menuSelectedUncle" href="departments/recreation.php" target="_self">Community Center</a></li>
			<li class="menuLI level1 menuSelectedUncle li-24"><a class="menuA level1 menuSelectedUncle" href="departments/utility_billing_customer_service.php" target="_self">Customer Service</a></li>
			<li class="menuLI level1 menuSelectedUncle li-28"><a class="menuA level1 menuSelectedUncle" href="departments/finance.php" target="_self">Finance</a></li>
			<li class="menuLI level1 menuSelectedUncle li-204"><a class="menuA level1 menuSelectedUncle" href="departments/electric.php" target="_self">Electric</a></li>
			<li class="menuLI level1 menuSelectedUncle li-33"><a class="menuA level1 menuSelectedUncle" href="departments/fire.php" target="_self">Fire</a></li>
			<li class="menuLI level1 menuSelectedUncle li-34"><a class="menuA level1 menuSelectedUncle" href="departments/library.php" target="_self">Library</a></li>
			<li class="menuLI level1 menuSelectedUncle li-35"><a class="menuA level1 menuSelectedUncle" href="departments/police_(sheriff).php" target="_self">Police (Sheriff)</a></li>
			<li class="menuLI level1 menuSelectedUncle li-213"><a class="menuA level1 menuSelectedUncle" href="departments/streets.php" target="_self">Streets/Stormwater</a></li>
			<li class="menuLI level1 menuSelectedUncle li-214"><a class="menuA level1 menuSelectedUncle" href="departments/parks.php" target="_self">Parks</a></li>
			<li class="menuLI level1 menuSelectedUncle li-215"><a class="menuA level1 menuSelectedUncle" href="departments/water_wastewater.php" target="_self">Water/Wastewater</a></li>
			<li class="menuLI level1 menuSelectedUncle li-38"><a class="menuA level1 menuSelectedUncle" href="departments/faq.php" target="_self">FAQ</a></li>
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
            RZ.nexturl = "editforms/slider-editlist.jsp?pageid=5";
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
			  RZ.nexturl = "/revize/plugins/menus/webspace_menu-editlist.jsp?pageid=links-21&"
			           + "linksfilter=linkplacement=leftnav and linkparentid=5::linkplacement=leftnav and linkparentid=21&"
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
	<li id="li-94" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/administration.php" target="_self" >Administration</a></li>
	<li id="li-95" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/building.php" target="_self" >Building</a></li>
	<li id="li-97" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/community_development.php" target="_self" >Community Development</a></li>
	<li id="li-98" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/utility_billing_customer_service.php" target="_self" >Utility Billing/Customer Service</a></li>
	<li id="li-99" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/finance.php" target="_self" >Finance</a></li>
	<li id="li-100" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/fire.php" target="_self" >Fire</a></li>
	<li id="li-101" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/recreation.php" target="_self" >Recreation</a></li>
	<li id="li-102" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/library.php" target="_self" >Library</a></li>
	<li id="li-103" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/police_(sheriff).php" target="_self" >Police (Sheriff)</a></li>
	<li id="li-106" class="menuLI level0 menuHidden"><a class="menuA level0 menuHidden" href="departments/faq.php" target="_self" >FAQ</a></li>
</ul>

			  <!-- end plugin: menus.leftnav-section -->
		</aside><!--/#flyout-wrap-->
		<article id="entry">
			<div id="breadcrumbs">

<a href="./">Home</a> &nbsp;&nbsp;<a href="departments/index.php">Departments</a> &nbsp;&nbsp;Building
</div><!-- /#breadcrumbs -->
			<h2 id="page-title">

  


Building
</h2>
			<div class="centerBtns">
	
        
            <script language="JavaScript" type="text/JavaScript">
                RZ.module = 'freeform';
                RZ.recordid = '';
                RZ.nexturl = "editforms/freeform-editform.jsp";
                RZ.img = '<span class="rzBtn">Edit Content</span>';
                RZ.set = 'freeform.pageid=links-21';
                RZ.options = '';
                if (typeof RZaction != 'undefined') RZaction('editform');
            </script>
    
    
		<script language="JavaScript" type="text/JavaScript">
            RZ.module = 'freeform';
            RZ.recordid = '';
            RZ.nexturl = "editforms/metadata-editform.jsp";
            RZ.popupwidth = ''; RZ.popupheight = ''; RZ.popupscroll = '';
            RZ.img = '<span class="rzBtn">Edit Metadata</span>';
            RZ.set = "freeform.pageid=links-21";
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



<div id="post">
    <p data-start="184" data-end="243"><span style="font-size: 18px;"><strong data-start="184" data-end="198">Lisa Bolin</strong></span><br data-start="198" data-end="201" /><span style="font-size: 18px;"><strong data-start="201" data-end="222">Permit Technician</strong></span><br data-start="222" data-end="225" /><span style="font-size: 18px;">City of Fort Meade</span></p>
<p data-start="245" data-end="302">&#128205; <strong data-start="248" data-end="261">Location:</strong><br data-start="261" data-end="264" />20 Langford St.<br data-start="279" data-end="282" />Fort Meade, FL 33841</p>
<p data-start="304" data-end="421">&#128222; <strong data-start="307" data-end="317">Phone:</strong> (863) 285-1100 ext. 221<br data-start="341" data-end="344" />&#9993;&#65039; <strong data-start="347" data-end="357">Email:</strong> <a class="cursor-pointer" rel="noopener" data-start="358" data-end="421">lbolin@cityoffortmeade.org<br /><br /></a><strong style="font-size: 12pt; color: #304753;"><strong><a href= "residents/coronavirus_(covid-19)/index.php"></a><br /><a href= "LDR 10-27-21.pdf?t=202206140808150"  target="_blank"  >Fort Meade Land Development Code</a><br />&nbsp;Apply for Permits<br /></strong></strong><span style="font-size: 12pt;"><strong><a href="https://www.polk-county.net/accela-info" target="_blank"><img class="th" title="icon-CitizenPortal" src="http://web.archive.org/web/20181121180246im_/https://www.polk-county.net/images/default-source/bocc-images/icon-tile-images/icon-citizenportal.jpg?sfvrsn=2" alt="icon-CitizenPortal" data-displaymode="Original" /></a></strong></span></p>
<hr data-start="423" data-end="426" />
<h3 data-start="428" data-end="466">Permit &amp; Land Development Services</h3>
<p data-start="468" data-end="629">The Permit Technician is responsible for administering permit applications, reviews, and inspections in accordance with the <strong data-start="592" data-end="628">Fort Meade Land Development Code</strong>.</p>
<hr data-start="631" data-end="634" />
<h3 data-start="636" data-end="656">Responsibilities</h3>
<ul data-start="658" data-end="847">
<li data-start="658" data-end="682">
<p data-start="660" data-end="682">Building Inspections</p>
</li>
<li data-start="683" data-end="716">
<p data-start="685" data-end="716">Commercial Safety Inspections</p>
</li>
<li data-start="717" data-end="748">
<p data-start="719" data-end="748">Minimal Housing Inspections</p>
</li>
<li data-start="749" data-end="781">
<p data-start="751" data-end="781">Issuance of Building Permits</p>
</li>
<li data-start="782" data-end="818">
<p data-start="784" data-end="818">Commercial Building Plans Review</p>
</li>
<li data-start="819" data-end="847">
<p data-start="821" data-end="847">Residential Plans Review</p>
</li>
</ul>
<hr data-start="849" data-end="852" />
<h3 data-start="854" data-end="877">Do I Need a Permit?</h3>
<p data-start="879" data-end="928">A <strong data-start="881" data-end="912">building permit is required</strong> if you plan to:</p>
<ul data-start="930" data-end="1189">
<li data-start="930" data-end="1010">
<p data-start="932" data-end="1010">Construct, enlarge, alter, repair, move, or demolish a building or structure</p>
</li>
<li data-start="1011" data-end="1056">
<p data-start="1013" data-end="1056">Change the occupancy or use of a building</p>
</li>
<li data-start="1057" data-end="1189">
<p data-start="1059" data-end="1189">Install, alter, repair, or replace any <strong data-start="1098" data-end="1112">electrical</strong>, <strong data-start="1114" data-end="1126">plumbing</strong>, <strong data-start="1128" data-end="1142">mechanical</strong>, or <strong data-start="1147" data-end="1154">gas</strong> system (per Florida Building Code)</p>
</li>
</ul>
<p data-start="1191" data-end="1372">Per <strong data-start="1195" data-end="1226">Florida Statute Chapter 489</strong>, licensed contractors are typically required to perform permitted work, except in limited cases for owner-occupied single-family or duplex homes.</p>
<p data-start="1374" data-end="1508"><strong data-start="1374" data-end="1402">You DO NOT need a permit</strong> for basic cosmetic updates such as painting, wallpaper, installing tile or carpet, or replacing cabinets.</p>
<hr data-start="1510" data-end="1513" />
<h3 data-start="1515" data-end="1554">Examples of Work Requiring a Permit</h3>
<ul data-start="1556" data-end="2290">
<li data-start="1556" data-end="1589">
<p data-start="1558" data-end="1589">Structural changes or framing</p>
</li>
<li data-start="1590" data-end="1644">
<p data-start="1592" data-end="1644">Load-bearing and non-load-bearing wall alterations</p>
</li>
<li data-start="1645" data-end="1695">
<p data-start="1647" data-end="1695">Enclosing carports, porches, or screened rooms</p>
</li>
<li data-start="1696" data-end="1757">
<p data-start="1698" data-end="1757">Building decks (attached or detached, roofed or unroofed)</p>
</li>
<li data-start="1758" data-end="1797">
<p data-start="1760" data-end="1797">Roofing installation or replacement</p>
</li>
<li data-start="1798" data-end="1844">
<p data-start="1800" data-end="1844">Electrical, plumbing, and HVAC system work</p>
</li>
<li data-start="1845" data-end="1901">
<p data-start="1847" data-end="1901">Installing or replacing windows, doors, or skylights</p>
</li>
<li data-start="1902" data-end="1945">
<p data-start="1904" data-end="1945">Installing hurricane shutters or siding</p>
</li>
<li data-start="1946" data-end="1989">
<p data-start="1948" data-end="1989">Installing or repairing fences or gates</p>
</li>
<li data-start="1990" data-end="2035">
<p data-start="1992" data-end="2035">Constructing or demolishing any structure</p>
</li>
<li data-start="2036" data-end="2079">
<p data-start="2038" data-end="2079">Site work, driveways, patios, sidewalks</p>
</li>
<li data-start="2080" data-end="2117">
<p data-start="2082" data-end="2117">Installing swimming pools or spas</p>
</li>
<li data-start="2118" data-end="2141">
<p data-start="2120" data-end="2141">Fire damage repairs</p>
</li>
<li data-start="2142" data-end="2207">
<p data-start="2144" data-end="2207">Commercial kitchen exhausts, fire sprinklers, or grease traps</p>
</li>
<li data-start="2208" data-end="2252">
<p data-start="2210" data-end="2252">Permanent signage, awnings, and canopies</p>
</li>
<li data-start="2253" data-end="2290">
<p data-start="2255" data-end="2290">Installing sheds or storage units</p>
</li>
</ul>
<h3><span style="font-size: 12pt;"><em><em><em><em><em><em><em>Helpful Links:<br /><a href="https://www.polk-county.net/" target="_blank">Polk County BoCC</a><br /><a href="https://www.polkpa.org/" target="_blank">Polk County Property Appraiser</a><br /><a href="http://www.polktaxes.com/" target="_blank">Polk County Tax Collector</a><br /><a href="http://www.leg.state.fl.us/Welcome/index.cfm?CFID=164567786&amp;CFTOKEN=40457073" target="_blank">Florida Statutes</a></em></em></em></em></em></em></em></span></h3>
<p><span style="font-size: 12pt;">&nbsp;</span></p>
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
               
                <a href="https://cms2.revize.com/revize/security/index.jsp?webspace=fortmeadefl&filename=/departments/building.php" id="revize-login">Login</a>
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
					<pre>&lt;a href="http://www.cityoffortmeade.org/departments/building.php">Your Link Name&lt;/a&gt;</pre>
				</div><!-- /.copylink -->
				<div class="share-btns">
					<p>Share this page on your favorite Social network</p>
					<div class="row">
						<div class="col-md-3 col-xs-6">
							<a href="https://www.facebook.com/sharer/sharer.php?u=http://www.cityoffortmeade.org/departments/building.php" class="btn-facebook" onclick="return !window.open(this.href, 'facebook ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-facebook"></i> Facebook
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.twitter.com/home?status=http://www.cityoffortmeade.org/departments/building.php" class="btn-twitter" onclick="return !window.open(this.href, 'twitter ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-twitter"></i> Twitter
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.plus.google.com/share?url=http://www.cityoffortmeade.org/departments/building.php" class="btn-google" onclick="return !window.open(this.href, 'google ', 'width=500,height=500')"
							target="_blank">
								<i class="fa fa-google-plus"></i> Google Plus
							</a>
						</div>
						<div class="col-md-3 col-xs-6">
							<a href="https://www.reddit.com/submit?url=http://www.cityoffortmeade.org/departments/building.php" class="btn-reddit" onclick="return !window.open(this.href, 'redit ', 'width=500,height=500')"
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
