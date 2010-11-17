
$(document).ready(function() {
	$('#addtest-container').hide();
	$('.submitbtn-progress').hide();
	$('.startbtn-progress').hide();
	$('#phone-prompt').hide();
	
	// add click action to the add-test button
    $('.add-btn').click(function() {
        $('#addtest-container').slideDown();
      });
    
    $('.startbtn').click(function() {
    	$(this).find('.startbtn-progress').show();
    	$(this).parent().find('.wordlist').hide();
        postData = 'id='+$(this).attr('testid');
        $.ajax({
        	type: 'POST',
        	url: '/test/start',
        	data: postData,
        	dataType: 'xml',
        	success: function(xml) {
        	  alert('Your phone will ring shortly with the test!');
         	  $('.startbtn-progress').hide();
            },
            failure: function(xml) {
            	alert(xml);
            },
        }); 
    });
    
    $('.recordwordbtn').click(function() {
    	$(this).find('.startbtn-progress').show();
        postData = 'code='+$(this).attr('code')+'&index='+$(this).attr('index');
        $.ajax({
        	type: 'POST',
        	url: '/record/recordword',
        	data: postData,
        	dataType: 'xml',
        	success: function(xml) {
        	  alert('Your phone will ring shortly for you to record your word!');
         	  $('.startbtn-progress').hide();
            },
            failure: function(xml) {
            	alert(xml);
            },
        }); 
    });

    // mouse-over for table rows
    $(".add-btn").mouseover(function() {
        $(this).addClass('add-btn-highlighted');
    });

	$(':input','#myform')
	 .not(':button, :submit, :reset, :hidden')
	 .val('')
	 .removeAttr('checked')
	 .removeAttr('selected');

    var options = { 
            target:        '#output2',   // target element(s) to be updated with server response 
            beforeSubmit:  showRequest,  // pre-submit callback 
            success:       showResponse,  // post-submit callback 
     
            url: '/addtest',         // override for form's 'action' attribute 
            type: 'post',        // 'get' or 'post', override for form's 'method' attribute 
            dataType:  'json',        // 'xml', 'script', or 'json' (expected server response type) 
            clearForm: true        // clear all form fields after successful submit 

            // other available options: 
            //resetForm: true        // reset the form after successful submit 
     
            // $.ajax options can be used here too, for example: 
            //timeout:   3000 
        }; 
     
        // bind to the form's submit event 
        $('.addtest-form').submit(function() { 
            // inside event callbacks 'this' is the DOM element so we first 
            // wrap it in a jQuery object and then invoke ajaxSubmit 
            $(this).ajaxSubmit(options); 
     
            // !!! Important !!! 
            // always return false to prevent standard browser submit and page navigation 
            return false; 
        }); 
     
}); // ready function

// pre-submit callback 
function showRequest(formData, jqForm, options) { 
    // formData is an array; here we use $.param to convert it to a string to display it 
    // but the form plugin does this for you automatically when it submits the data 
    var queryString = $.param(formData); 
 
    // jqForm is a jQuery object encapsulating the form element.  To access the 
    // DOM element for the form do this: 
    // var formElement = jqForm[0]; 
 
    //alert('About to submit: \n\n' + queryString); 
	$('.submitbtn-progress').show();

	// here we could return false to prevent the form from being submitted; 
    // returning anything other than false will allow the form submit to continue 
    return true; 
} 
 
// post-submit callback 
function showResponse(test, statusText, xhr, $form)  { 
    // if the ajaxSubmit method was passed an Options Object with the dataType 
    // property set to 'json' then the first argument to the success callback 
	// is the json data object returned by the server
	$('.submitbtn-progress').hide();
	$("#addtest-container").slideUp();
	$("#inventory #test:first").before(
			"<div id='test'>" +
			"<span class='owner'>"+test.name+"</span>" +
			"<p>grade: "+test.grade+"</p>" +
			"<p>words: "+test.words+"</p>" +
			"</div>");
	$(window.location).attr('href', '/');

} 
