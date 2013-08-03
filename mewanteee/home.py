print 'Content-Type: text/html'
print ''
print '<center><b>ME WANTEE!</b></center>'
print '<br><br><br><br><br><br><br>'
print '<br><br><br><br><br><br><br>'
print '<br><br><br><br><br><br><br>'

# google analytics
print """
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
var pageTracker = _gat._getTracker("UA-1790845-3");
pageTracker._trackPageview();
</script>
"""

# ads
print """
<script type="text/javascript"><!--
google_ad_client = "pub-3567472245202712";
/* 728x90, created 9/11/08 */
google_ad_slot = "7554612788";
google_ad_width = 728;
google_ad_height = 90;
//-->
</script>
<script type="text/javascript"
src="http://pagead2.googlesyndication.com/pagead/show_ads.js">
</script>
"""
