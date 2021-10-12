
	<script>
		var mapinterval = null;
		var countcheck = 0;
		var urlstring = null;
		
	$(document).ready(function(){
		
		var mymap = L.map('mapid').setView([51.457861, -0.979969], 13);
var mapinfo = {};
	L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw', {
		maxZoom: 18,
		attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, ' +
			'<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
			'Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
		id: 'mapbox.streets'
	}).addTo(mymap);
		
		
		
		var areaSelect = L.areaSelect({width:200, height:300});
areaSelect.addTo(mymap);
		
		
		// Read the bouding box
var bounds = areaSelect.getBounds();
		updatepos();

// Get a callback when the bounds change
areaSelect.on("change", function() {
	
	updatepos();

});
		
function updatepos() {
	var bounds = areaSelect.getBounds();
		$("#maxlat").val(bounds['_northEast']['lat']);
	$("#maxlon").val(bounds['_northEast']['lng']);
	$("#minlat").val(bounds['_southWest']['lat']);
	$("#minlon").val(bounds['_southWest']['lng']);
	var dims = areaSelect.getDimensions();
	$("#x_mm").val(dims['x_mm']);
	$("#y_mm").val(dims['y_mm']);
}
		
$("#x_mm").on('input', function()  {
	var xmm = Math.round($(this).val());
  areaSelect.setDimensions({width: xmm});
});
		$("#y_mm").on('input', function()  {
			var ymm = Math.round($(this).val());
  areaSelect.setDimensions({height: ymm});
});
		
		$(".mapform").on('input', function() {
			var validdata = true;
			if ($('#useremail').val() == '' || isEmail($('#useremail').val()) == false) {
				validdata = false;
			}
			if ($('#fullname').val() == '') {
				validdata = false;
			}
				$("#downloadbutton").hide();
			
			if (validdata) {
				$('.bigbutton').removeClass('inactive');
				
		$('#generatebutton').show();
			} else {
				$('.bigbutton').addClass('inactive');
			}
				});
		
		$("#generatebutton").on('click',function() {
			
			var layers = new Array();
			$(".mapform input[type=checkbox]:checked").each(function() {
  				layers.push($(this).val());
					});
			mapinfo = [];
			mapinfo = {
     				"user" : {
        				"name": $('#fullname').val(),
						"email": $('#useremail').val()
					},
				"bounds" : {
        				"minlat": $('#minlat').val(),
						"minlon": $('#minlon').val(),
						"maxlat": $('#maxlat').val(),
						"maxlon": $('#maxlon').val(),
						"x_mm": $('#x_mm').val(),
						"y_mm": $('#y_mm').val()
					},
				"contours" : {
        				"interval": $('#contour_interval').val()
					},
				"layers" : layers
			};

			
			var myJSON = JSON.stringify(mapinfo);
			
			var formJx = postMap(myJSON);
			$(this).hide();
			$('#generating').show();
			
			$("#jsonout").val(myJSON);
			
		});
		
		
		
		
					  
					  
 		
	});
		
		
		function isEmail(email) {
  var regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
  return regex.test(email);
}
		
		
		
		
function postMap(datastream) {
    // Creating the XMLHttpRequest object
    var request = new XMLHttpRequest();
    
    // Instantiating the request object
    request.open("POST", "https://maptolaser.geo-fun.org");
    request.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    // Defining event listener for readystatechange event
    request.onreadystatechange = function() {
        // Check if the request is compete and was successful
        if(this.readyState === 4 && this.status === 200) {
            // Inserting the response from server into an HTML element
            document.getElementById("response").innerHTML = JSON.stringify( this.responseText );
			
			urlstring = "https://maptolaser.geo-fun.org/"+this.responseText;
			
			$("#downloadbutton").attr("href", urlstring);
			$("#downloadbutton").attr("download", this.responseText+".svg");
			
			
			mapinterval = setInterval("checkmapsvg(urlstring)", 5000);
			


        }

	}
    // Sending the request to the server
    request.send(datastream);
}

		
		
		
	function checkmapsvg(url) {	
		countcheck = countcheck + 1;
		
		var client = new XMLHttpRequest();
client.open("GET", url, true);
client.send();

client.onreadystatechange = function() {
  if(client.readyState == client.HEADERS_RECEIVED) {
    var contentType = client.getResponseHeader("Content-Type");
	  document.getElementById("response").innerHTML = countcheck+"; "+contentType+" / "+client.responseText;
console.log('response', client.responseText);
    if (contentType == "image/svg+xml") {
      clearInterval(mapinterval);
		$("#downloadbutton").show();
		$('#generating').hide();
    }
  };
}
	}
		
	</script>