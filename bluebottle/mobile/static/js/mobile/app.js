window.token = localStorage.getItem('jwtToken');

$(document).ready(function(){
    var userProfileHandler = Handlebars.compile($("#user-tpl").html());
    var loginHandler = Handlebars.compile($("#login-tpl").html());
    var projectListHandler = Handlebars.compile($("#project-preview-tpl").html());
    var projectHandler = Handlebars.compile($("#project-tpl").html());

    var toast = function(msg){
        $("<div class='ui-loader ui-overlay-shadow ui-body-e ui-corner-all'><h3>"+msg+"</h3></div>")
        .css({ display: "block",
            opacity: 0.90,
            backgroundColor: '#333',
            position: "fixed",
            padding: "7px",
            "text-align": "center",
            width: "270px",
            left: ($(window).width() - 284)/2,
            top: $(window).height()/2 })
        .appendTo( $.mobile.pageContainer ).delay( 1500 )
        .fadeOut( 400, function(){
            $(this).remove();
        });
    };

    var loadProjects = function(search, page){
        $.ajax({
            type: "GET",
            url: "/api/bb_projects/previews?ordering=popularity&status=5&page=" + page,
            success: function (data) {
                $.each(data.results, function(i, row) {
                    $('#project-list').append(projectListHandler(row));
                });
                $("#projects").trigger("create");
                $("#project-list").listview();
            }
        });
    };

    var getUser = function(){
        $.ajax({
            type: "GET",
            url: "/api/users/current",
            beforeSend: function (xhr) {
                xhr.setRequestHeader("Authorization", "JWT " + window.token);
            },
            success: function (data) {
                $('#user').html(userProfileHandler(data));
                $('#logout').on('click', function(){
                    window.token = '';
                    localStorage.setItem('jwtToken', '');
                     $('#user').html(loginHandler());
                });
            },
            error: function(){
                 $('#user').html(loginHandler());
            }
        });
    };
    var getProject = function(id){
        $('#project-detail').empty();
        $.ajax({
            type: "GET",
            url: "/api/bb_projects/projects/" + id,
            success: function (data) {
                $('#project-detail').html(projectHandler(data));
                $("#project").trigger("create");

                var photo_id;

                $('.post-update input[type=file]').on('change', function (event) {

                    // Handle file upload
                    var files = event.target.files;
                    var data = new FormData();
	                $.each(files, function(key, value){
		                data.append('photo', value);
                    });

                    $.ajax({
                        url: '/api/wallposts/photos/',
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader("Authorization", "JWT " + window.token);
                        },
                        type: 'POST',
                        data: data,
                        cache: false,
                        dataType: 'json',
                        processData: false, // Don't process the files
                        contentType: false, // Set content type to false as jQuery will tell the server its a query string request
                        success: function(data, textStatus, jqXHR){
                            photo_id = data.id;
                        }
                    });
                });

                $('.post-update').on('submit', function (event) {
                    event.preventDefault();
                    var post = $('.post-update').serialize();

                    $.ajax({
                        type: 'POST',
                        data: post,
                        url: "/api/wallposts/mediawallposts/",
                        beforeSend: function(xhr) {
                            xhr.setRequestHeader("Authorization", "JWT " + window.token);
                        },
                        success: function(data){
                            // Connect photo to the wallpost
                            if (photo_id) {
                                var photo = {'mediawallpost': data.id, 'id': photo_id};
                                $.ajax({
                                    type: 'PUT',
                                    data: photo,
                                    url: "/api/wallposts/photos/" + photo_id,
                                    beforeSend: function(xhr) {
                                        xhr.setRequestHeader("Authorization", "JWT " + window.token);
                                    },
                                    success: function(){
                                        toast('Posted! Thanks for your update.');
                                        $('.post-update').find("input, textarea").val("");
                                    }
                                })
                            } else {
                                toast('Posted! Thanks for your update.');
                                $('.post-update').find("input, textarea").val("");
                            }
                        }
                    });
                });

            }
        });
    };


    $(document).on('vclick', '#project-list li a', function(){
        getProject($(this).attr('data-id'));
        $.mobile.changePage( "#project", { transition: "slide", changeHash: false });
    });

    $(document).on('vclick', '#load-more-projects', function(){
        projectPage++;
        loadProjects(projectSearch, projectPage);
    });



    $('.login').on('submit', function (e) {
        var credentials = $('.login').serialize();
        $.post("/api/token-auth/", credentials, function (auth) {
            window.token = auth.token;
            localStorage.setItem('jwtToken', auth.token);
            getUser();
        });
    });

    // Init some things

    var projectPage = 1,
        projectSearch = '';
    loadProjects(projectSearch, projectPage);

    if (window.token) {
        getUser();
    } else {
        $('#user').html(loginHandler());
    }

});


