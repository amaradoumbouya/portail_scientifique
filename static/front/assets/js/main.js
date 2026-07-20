(function($) {
    "use strict";

    // Preloader
    $(window).on('load', function() {
        $("#loading").fadeOut(1200);
    });

    // Sticky Nav1
    $(document).on("scroll", function() {
        if ($(document).scrollTop() > 150) {
            $(".main-nav").addClass("black");
        } else {
            $(".main-nav").removeClass("black");
        }
    });

    // Sticky Nav2
    $(document).on("scroll", function() {
        if ($(document).scrollTop() > 0) {
            $(".mobile-nav").addClass("black");
        } else {
            $(".mobile-nav").removeClass("black");
        }
    });

    // Scroll Top
    $(window).on("scroll", function() {
        if ($(this).scrollTop() > 0) {
            $('.scroll-top').fadeIn();
        } else {
            $('.scroll-top').fadeOut();
        }
    });
    $('.scroll-top').click(function() {
        $('html, body').animate({
            scrollTop: 0
        }, 500);
        return false;
    });

    // Mean Menu
    jQuery('.mean-menu').meanmenu({
        meanScreenWidth: "991"
    });

    // Wow  JS
    new WOW({
        offset: 100,
        mobile: true
    }).init();

    // Magnific PopUp
    $(".video-pop").magnificPopup({
        disableOn: 320,
        type: 'iframe',
        removalDelay: 160,
        preloader: false,
        fixedContentPos: false
    });

    // Owl Carausel 
    var $homeCourseSlider = $('.home-course-slider');
    if ($homeCourseSlider.length && $homeCourseSlider.children().length) {
        var homeCourseCount = $homeCourseSlider.children().length;
        $homeCourseSlider.owlCarousel({
            loop: homeCourseCount > 4,
            margin: 20,
            dots: false,
            autoplay: homeCourseCount > 1,
            nav: homeCourseCount > 1,
            navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
            autoplayHoverPause: true,
            responsive: {
                0: {
                    items: 1,
                },
                576: {
                    items: Math.min(2, homeCourseCount),
                },
                768: {
                    items: Math.min(2, homeCourseCount),
                },
                1000: {
                    items: Math.min(3, homeCourseCount),
                },
                1300: {
                    items: Math.min(4, homeCourseCount),
                }
            }
        });
    }

    var $courseSlider = $('.course-slider');
    if ($courseSlider.length && $courseSlider.children().length) {
        $courseSlider.owlCarousel({
            loop: $courseSlider.children().length > 1,
            margin: 20,
            dots: false,
            autoplay: false,
            nav: $courseSlider.children().length > 1,
            navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
            autoplayHoverPause: true,
            responsive: {
                0: {
                    items: 1,
                },
                576: {
                    items: 1,
                },
                768: {
                    items: 1,
                },
                1200: {
                    items: 1,
                }
            }
        });
    }

    $(".home-slider").owlCarousel({
        items: 1,
        loop: true,
        autoplay: true,
        autoplayTimeout: 6000,
        autoplayHoverPause: true,
        autoplaySpeed: 800,
        smartSpeed: 800,
        dots: false,
        nav: true,
        navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
        mouseDrag: true,
        touchDrag: true,
        pullDrag: true,
        responsive: {
            0: {
                items: 1,
            },
            576: {
                items: 1,
            },
            768: {
                items: 1,
            },
            1200: {
                items: 1,
            }
        }

    });

    $('.event-slider').owlCarousel({
        loop: true,
        margin: 20,
        dots: false,
        autoplay: false,
        dots: false,
        autoplayHoverPause: true,
        mouseDrag: false,
        navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
        responsive: {
            0: {
                items: 1,
            },
            576: {
                items: 1,
            },
            768: {
                items: 1,
            },
            1200: {
                items: 1,
            }
        }
    });
    $('.news-slider').owlCarousel({
        loop: true,
        margin: 20,
        dots: false,
        autoplay: false,
        dots: false,
        autoplayHoverPause: true,
        mouseDrag: false,
        navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
        responsive: {
            0: {
                items: 1,
            },
            576: {
                items: 1,
            },
            768: {
                items: 1,
            },
            1200: {
                items: 1,
            }
        }
    });

    $('.teacher-slider').owlCarousel({
        loop: true,
        margin: 20,
        dots: false,
        autoplay: false,
        dots: false,
        autoplayHoverPause: true,
        mouseDrag: false,
        navText: ["<i class='flaticon-left-arrow'></i>", "<i class='flaticon-next'></i>"],
        responsive: {
            0: {
                items: 1,
            },
            576: {
                items: 1,
            },
            768: {
                items: 1,
            },
            1200: {
                items: 1,
            }
        }
    });

    // Gallery
    $('.image-pop').magnificPopup({
        type: 'image',
        removalDelay: 300,
        gallery: {
            enabled: true
        },
    });

    // FAQ Accordion
    $('.accordion').find('.accordion-title').on('click', function() {
        $(this).toggleClass('active');
        $(this).next().slideToggle('fast');
        $('.accordion-content').not($(this).next()).slideUp('fast');
        $('.accordion-title').not($(this)).removeClass('active');
    });

    // Count Time 
    function makeTimer() {
        var deadlineEl = document.querySelector('.admission-content[data-deadline]');
        var deadlineValue = deadlineEl ? deadlineEl.getAttribute('data-deadline') : null;
        var endTime = deadlineValue
            ? new Date(deadlineValue)
            : new Date(new Date().getFullYear(), 2, 30, 23, 59, 59);

        // Si la date de l'année en cours est déjà passée, basculer sur l'année suivante
        if (!deadlineValue && endTime.getTime() < Date.now()) {
            endTime = new Date(new Date().getFullYear() + 1, 2, 30, 23, 59, 59);
        }

        var endTimeSec = Date.parse(endTime) / 1000;
        var nowSec = Date.parse(new Date()) / 1000;
        var timeLeft = Math.max(0, endTimeSec - nowSec);
        var days = Math.floor(timeLeft / 86400);
        var hours = Math.floor((timeLeft - (days * 86400)) / 3600);
        var minutes = Math.floor((timeLeft - (days * 86400) - (hours * 3600)) / 60);
        var seconds = Math.floor((timeLeft - (days * 86400) - (hours * 3600) - (minutes * 60)));
        if (hours < 10) {
            hours = "0" + hours;
        }
        if (minutes < 10) {
            minutes = "0" + minutes;
        }
        if (seconds < 10) {
            seconds = "0" + seconds;
        }
        $("#days").html(days + "");
        $("#hours").html(hours + "");
        $("#minutes").html(minutes + "");
        $("#seconds").html(seconds + "");
    }
    setInterval(function() {
        makeTimer();
    }, 1000);

    // Isotope Filter
    $('.gall-list').isotope({
        itemSelector: '.item'
    });
    $('.all-gall li').click(function() {
        $('.all-gall li').removeClass('active');
        $(this).addClass('active');
        var selector = $(this).attr('data-filter');
        $('.gall-list').isotope({
            filter: selector
        });
        return false;
    });

    // Switch Btn
	$('body').append("<div class='switch-box'><label id='switch' class='switch'><input type='checkbox' onchange='toggleTheme()' id='slider'><span class='slider round'></span></label></div>");

}(jQuery));

// function to set a given theme/color-scheme
function setTheme(themeName) {
    localStorage.setItem('edvi_theme', themeName);
    document.documentElement.className = themeName;
}
// function to toggle between light and dark theme
function toggleTheme() {
    if (localStorage.getItem('edvi_theme') === 'theme-dark') {
        setTheme('theme-light');
    } else {
        setTheme('theme-dark');
    }
}
// Immediately invoked function to set the theme on initial load
(function () {
    if (localStorage.getItem('edvi_theme') === 'theme-dark') {
        setTheme('theme-dark');
        document.getElementById('slider').checked = false;
    } else {
        setTheme('theme-light');
      document.getElementById('slider').checked = true;
    }
})();