
$(function(){
		
	//Other UI stuff
	$("#file-stash-h").click(function(){
		var arrowSpan = $("span#toggle-arrow-file-stash");
		if (arrowSpan.hasClass("down")){
			arrowSpan.removeClass("down");
			arrowSpan.addClass("up");
			arrowSpan.html("&#9650");			
			$.get("/ui/file_stash.html", function(data){
				$("#file-stash-div").html(data).show();
			});
		}
		else{
			arrowSpan.removeClass("up");
			arrowSpan.addClass("down");
			arrowSpan.html("&#9660");
			$("#file-stash-div").toggle();
		}
	});
	
});

$(window).load(function() {
	  function updateJobs(){
			$.get( "/ui/jobs/current", function( data ) {
	  			$( "#current-job" ).html( data );
			});
			$.get( "/ui/jobs/past", function( data ) {
				$( "#past-jobs" ).html( data );
			});
			$.get( "/ui/jobs/pending", function( data ) {
				$( "#pending-jobs" ).html( data );
			});
	  }
      var uploader = new plupload.Uploader({
			runtimes : 'gears,html5,browserplus',
			browse_button : 'pickfiles',
			container : 'file-container',
			max_file_size : '1000mb',
			url : '/ui/upload',
			chunk_size : '5mb',
			unique_names : true,
			filters : [
				{title : "Zip files", extensions : "zip,rar"}
			],
		});

		uploader.bind('Init', function(up, params) {
			$('#filelist').html("<div>Current runtime: " + params.runtime + "</div>");
		});

		$('#uploadfiles').click(function(e) {
			uploader.start();
			e.preventDefault();
		});

		uploader.init();

		uploader.bind('FilesAdded', function(up, files) {
			$.each(files, function(i, file) {
				$('#filelist').append(
					'<div id="' + file.id + '">' +
					file.name + ' (' + plupload.formatSize(file.size) + ') <b></b>' +
				'</div>');
			});

			up.refresh(); // Reposition Flash/Silverlight
		});

		uploader.bind('UploadProgress', function(up, file) {
			$('#' + file.id + " b").html(file.percent + "%");
		});

		uploader.bind('Error', function(up, err) {
			$('#filelist').append("<div>Error: " + err.code +
				", Message: " + err.message +
				(err.file ? ", File: " + err.file.name : "") +
				"</div>"
			);

			up.refresh(); // Reposition Flash/Silverlight
		});

		uploader.bind('FileUploaded', function(up, file) {
			$('#' + file.id + " b").html("100%");
			updateJobs();
		});
});