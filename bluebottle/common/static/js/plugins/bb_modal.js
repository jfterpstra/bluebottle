BB = {};

BB.ModalControllerMixin = Em.Mixin.create({
    // This can be overridden with code to respond with when the 
    // modal content is about to be replaced with new content.
    // This will usually involve clearing the model data => form fields
    willClose: Em.K,

    // This can be overridden with code to respond with when the 
    // modal content is about to be displayed.
    willOpen: Em.K,

    actions: {
        close: function () {
            this.send('closeModal');
        }
    }
});

BB.ModalMixin = Em.Mixin.create({
    modalContainer: null,

    actions: {
        _disconnectContainerOutlet: function() {
            this.disconnectOutlet({
                outlet: 'modalContainer',
                parentView: 'application'
            });
        },

        closeModal: function() {
            this.send('_disconnectContainerOutlet');
        },

        openInDynamic: function(name, context) {
            this.send('openInBox', name, context, 'donation');
        },

        openInBox: function(name, context, type, callback) {
            // Setup the modal container
            var modalContainer = this.controllerFor('modalContainer');

            if (Em.isEmpty(type))
                modalContainer.set('type', 'normal');
            else
                modalContainer.set('type', type);

            this.render('modalContainer', {
                into: 'application',
                outlet: 'modalContainer',
                controller: modalContainer
            });

            this.set('modalContainer', modalContainer);

            // Handle any cleanup for the previously set content for the modal
            this.send('modalSlide', name, context);
        },

        modalBack: function (name) {
            this.get('modalContainer').jumpTo(name);
        },

        modalSlide: function (name, context) {
            // this.get('modalContainer')
            // var newController = this.controllerFor(name);
            this.get('modalContainer').push(name, context, 'slide');
        }
    },

    // actions: {
    //     _modalWillTransition: function(name, side, context) {
    //         // If the side is not defined then use the current displayed side
    //         if (! side || typeof side == 'undefined') {
    //             // The higher index is for the visible side.
    //             var frontIndex = parseInt($('#card .front').css('z-index')),
    //                 backIndex = parseInt($('#card .back').css('z-index'));

    //             side = frontIndex > backIndex ? 'modalFront' : 'modalBack';
    //         }

    //         // Handle any cleanup for the previously set content for the modal
    //         var modalContainer = this.controllerFor('modalContainer'),
    //             previousController = modalContainer.get('currentController');

    //         // Call willClose on the previous modal - if defined
    //         if (previousController && Em.typeOf(previousController.willClose) == 'function')
    //             previousController.willClose();


    //         // Set the currentController property on the container to this new controller
    //         // so we can call willClose on it later
    //         if (name) {
    //             var newController = this.controllerFor(name);
    //             modalContainer.set('currentController', newController);

    //             // Setup the modal content and set the model if passed
    //             if (Em.typeOf(context) != 'undefined')
    //                 newController.set('model', context);

    //             // Call willOpen on the new modal - if defined
    //             if (newController && Em.typeOf(newController.willOpen) == 'function')
    //                 newController.willOpen();

    //             this.render(name, {
    //                 into: 'modalContainer',
    //                 outlet: side,
    //                 controller: newController
    //             });
    //         }
    //     },

    //     _addRemoveClass: function(type, element, className, attrName, callback, animationEnd) {
    //         var i, amountElm = element.length;


    //         $('.flash-container').one(animationEnd, function(){
    //             if (callback === 'function') {
    //                 callback()
    //             }
    //         });

    //         for (var i = amountElm - 1; i >= 0; i--) {

    //             switch(type) {
    //                 case'add':
    //                     $(element[i]).addClass(className[i]);
    //                 break;
    //                 case'remove':
    //                     $(element[i]).removeClass(className[i]);
    //                 break;
    //                 case'attr':
    //                     $(element[i]).attr(attrName[i], className[i]);
    //                 break;
    //             }
    //         };
    //     },

    //     _disconnectContainerOutlet: function() {
    //         this.disconnectOutlet({
    //             outlet: 'modalContainer',
    //             parentView: 'application'
    //         });
    //     },

    //     _scrollDisable: function() {
    //         var $body = $('body');
    //         var oldWidth = $body.innerWidth();
    //         $body.width(oldWidth);
    //         $('#header').width(oldWidth);
    //         $body.addClass('is-stopped-scrolling');
    //     },

    //     _scrollEnable: function() {
    //         $('body').removeClass('is-stopped-scrolling');
    //         $('#header').width('');
    //         $('body').width('');
    //     },

    //     openInFullScreenBox: function(name, context) {
    //         this.send('openInBox', name, context, 'full-screen');
    //     },

    //     openInScalableBox: function(name, context) {
    //         this.send('openInBox', name, context, 'scalable');
    //     },

    //     openInBigBox: function(name, context) {
    //         this.send('openInBox', name, context, 'large');
    //     },

    //     openInDynamic: function(name, context) {
    //         this.send('openInBox', name, context, 'donation');
    //     },

    //     openInBox: function(name, context, type, callback) {
    //         // Setup the modal container
    //         var modalContainer = this.controllerFor('modalContainer');

    //         if (Em.isEmpty(type))
    //             modalContainer.set('type', 'normal');
    //         else
    //             modalContainer.set('type', type);

    //         this.render('modalContainer', {
    //             into: 'application',
    //             outlet: 'modalContainer',
    //             controller: modalContainer
    //         });

    //         this.send('_scrollDisable');
    //         this.send('closeKeyModal', '27');

    //         // Handle any cleanup for the previously set content for the modal
    //         this.send('_modalWillTransition', name, 'modalFront', context);
    //     },
        
    //     closeModal: function() {
    //         var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
    //             _this = this;

    //         // Handle any cleanup for the previously set content for the modal
    //         this.send('_modalWillTransition');

    //         if ($.browser.msie && parseInt($.browser.version) < 10){
    //             this.send('_disconnectContainerOutlet');
    //         }

    //         $('.modal-fullscreen-background').one(animationEnd, function(){
    //             // Finally clear the outlet
    //             _this.send('_disconnectContainerOutlet');
    //         });

    //         this.send('_scrollEnable');

    //         $('.modal-fullscreen-background').removeClass('is-active');
    //         $('.modal-fullscreen-background').addClass('is-inactive');
    //     },

    //     closeKeyModal: function(key) {
    //         var self = this;
    //         $(document).on('keydown', function(e) {
    //             if(e.keyCode == key) {
    //                 self.send('closeModal');
    //             }
    //         });
    //     },

    //     modalContent: function (name, context) {
    //         var controller = this.controllerFor(name);

    //         if (Em.typeOf(context) != 'undefined')
    //             controller.set('model', context);  

    //         this.send('_modalWillTransition', name, null, context);
    //     },

    //     modalFlip: function (name, context) {
    //         var controller = this.controllerFor(name);

    //         if (Em.typeOf(context) != 'undefined')
    //             controller.set('model', context);            

    //         if ($('#card').hasClass('flipped')) {
    //             $('#card').removeClass('flipped');
    //             modalSide = 'modalFront';
    //         } else {
    //             this.send('_addRemoveClass', 'attr', ['#card', '.front', '.back'], ['flipped', 'front', 'back'], ['class', 'class', 'class']);
    //             modalSide = 'modalBack';
    //         }

    //         // Handle any cleanup for the previously set content for the modal
    //         this.send('_modalWillTransition', name, modalSide, context);
    //     },

    //     modalSlide: function (name, context) {
    //         if ($('#card .front').hasClass('slide-out-left')) {
    //             this.send('modalSlideRight', name, context);
    //         } else {
    //             this.send('modalSlideLeft', name, context);
    //         }
    //     },

    //     modalSlideLeft: function(name, context) {
    //         // Handle any cleanup for the previously set content for the modal
    //         this.send('modalWillTransition', name, 'modalBack', context);
    //         if ($('#card').hasClass('flipped')) {
    //             $('#card').removeClass('flipped');
    //             $('#card').addClass('flipped-alt');
    //         } else {
    //             this.send('_addRemoveClass', 'add', ['.front', '.back'], ['slide-out-left', 'slide-in-right']);
    //         }

    //     },

    //     modalSlideRight: function(name, context) {
    //         var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
    //             _this = this;

    //         // Handle any cleanup for the previously set content for the modal
    //         if ($.browser.msie && parseInt($.browser.version) < 10){
    //             this.send('_modalWillTransition', 'modalFlip', 'modalFront', context);
    //             $('#card').removeClass('flipped');
    //             return;
    //         }
    //         this.send('_modalWillTransition', name, 'modalFront', context);
    //         if (!$('#card').hasClass('flipped')) {
    //             this.send('_addRemoveClass', 'remove', ['.front', '.back'], ['slide-out-left', 'slide-in-right']);
    //             this.send('_addRemoveClass', 'add', ['.front', '.back'], ['slide-in-left', 'slide-out-right']);
    //             $('#card').one(animationEnd, function(){
    //                 _this.send('_addRemoveClass', 'remove', ['.front', '.back'], ['slide-in-left', 'slide-out-right']);
    //             });
    //         }
    //     },

    //     modalScale: function(name, context) {
    //         this.send('_modalWillTransition', name, 'modalFront', context);
    //         this.send('_addRemoveClass', 'remove', ['.front', '.back'], ['scale-back', 'scale-down']);
    //         this.send('_addRemoveClass', 'add', ['.front', '.back'], ['scale-down', 'scale-up']);
    //     },

    //     modalScaleForward: function(name, context) {
    //         // Handle any cleanup for the previously set content for the modal
    //         this.send('_modalWillTransition', name, 'modalBack', context);
    //         this.send('_addRemoveClass', 'remove', ['.front', '.back'], ['scale-down', 'scale-up']);
    //         this.send('_addRemoveClass', 'add', ['.front', '.back'], ['scale-back', 'scale-down']);
    //     },

    //     modalScaleBack: function(name, context) {
    //         this.send('_modalWillTransition', name, 'modalFront', context);
    //         this.send('_addRemoveClass', 'remove', ['.front', '.back'], ['scale-back', 'scale-down']);
    //         this.send('_addRemoveClass', 'add', ['.front', '.back'], ['scale-down', 'scale-up']);
    //     },

    //     modalError: function() {
    //         var animationEnd = 'animationEnd animationend webkitAnimationEnd oAnimationEnd MSAnimationEnd',
    //             cardSide = $('#card.flipped'),
    //             cardSlide = $('.slide-in-right'),
    //             container;

    //         // Either cardSlide or cardSide will be defined if the back side is visible
    //         // otherwise it must be on the front side.
    //         if (Ember.isEmpty(cardSide) && Ember.isEmpty(cardSlide)) {
    //             // Front side is showing 
    //             container = $('#card .front .modal-fullscreen-item');
    //         } else {
    //             container = $('#card .back .modal-fullscreen-item');
    //         }

    //         container.addClass('is-shake').one(animationEnd, function(){
    //             container.removeClass('is-shake');
    //         });
    //     },

    //     modalIEreset: function(type, name, context, opt) {
    //         if ($.browser.msie && parseInt($.browser.version) < 10){
    //             switch(type) {
    //                 case 'normal':
    //                     this.send(name, context, opt);
    //                     console.log(type);
    //                 break;
    //             }
    //         }
    //     }
    // },
});

BB.ModalContainerController = Em.ArrayProxy.extend(Em.ControllerMixin, BB.ModalControllerMixin, {
    currentController: null,
    currentModalController: null,
    type: null,
    modalControllersBinding: 'content',

    init: function() {
        this._super();

        this.set('_modalControllers', Ember.A());
    },

    content: Ember.computed(function () {
        return Ember.A();
    }),

    // Push a class with optional context onto the stack. If the class can be 
    // found in the stack then it will be set as the current controller, 
    // otherwise the controller will be created first.
    push: function (controllerClass, object, transition) {
        if (!this.get('container')) {
            throw new Error('An instance of BB.ModalContainerController requires a container');
        }        

        this._renderModal(controllerClass, object, transition);
    },

    jumpTo: function (controllerClass, object, transition) {
        // First we need to find the matching modal controller
        var previousController = this.get('currentController'),
            modalController = this._matchModalController(controllerClass);

        // Found a match!
        if (modalController) {
            this._renderModal(controllerClass, object, transition);

            // And pop off any controllers between the matching controller
            // and the previous controller.
            var content = this.get('content'),
                previousIndex = content.indexOf(previousController),
                currentIndex = content.indexOf(modalController);

            for(i = currentIndex + 1; i <= previousIndex; i++) {
                this._destoryController(i);
            }
        } else {
            
        }

    },

    _destoryController: function (index) {
        this.get('content').removeAt(index, 1);
    },

    _renderModal: function (controllerClass, object, transition) {
        // Check if the class exists. The modalContainer controller
        // has an array of modalControllers and each of these has 
        // a 'frontController' and 'backController' property which 
        // is what needs to be matched against the class name passed.
        modalController = this.modalControllerFor(controllerClass, object, transition);

        this.container.lookup('route:application').render('modal', {
            into: 'modalContainer',
            outlet: 'currentModal',
            controller: modalController
        });

        // Set the controller on the front side of the modal
        modalController.setController('modalFront', controllerClass);
    },

    _matchControllerClass: function (targetController, controllerString) {
        return targetController && targetController.constructor.toString() == controllerString;
    },

    _matchModalController: function (controllerClass) {
        var _this = this,
            fullName = "controller:" + controllerClass,
            subControllerFactory = this.get('container').lookupFactory(fullName),
            subControllerStr = subControllerFactory.toString();

        var modalController = this.get('model').find(function (modal) {
            return _this._matchControllerClass(modal.get('frontController'), subControllerStr) || 
                    _this._matchControllerClass(modal.get('backController'), subControllerStr)
        });

        return modalController;
    },

    modalControllerFor: function(controllerClass, object, transition) {
        var _this = this,
            container = this.get('container'),
            modalControllers = this.get('model'),
            fullName = "controller:" + controllerClass,
            factory, fullName;

        if (! container.has(fullName)) {
            throw new Error('Could not resolve sub controller: "' + controllerClass + '"');
        }
        
        var modalController = this._matchModalController(controllerClass);

        if (modalController) {
            this.set('currentController', modalController);
            return modalController;
        }
        

        // Create a new modalController unless the transition is a flip
        // In the case of flipping then we use the other side of the 
        // current modalController.
        if (transition != 'flip') {
            modalController = container.lookupFactory('controller:modal').create({
                target: this,
                parentController: this.get('parentController') || this
            });
        } else {
            // If there is no currentModalController then we shouldn't be 
            // calling flip - throw error
            var currentModalController = this.get('currentModalController');

            if (! currentModalController) {
                throw new Error('Can\'t flip a modal without a currentModalController');
            } else {
                modalController = currentModalController;
            }
        }

        this.set('currentController', modalController);

        // subController = subControllerFactory.create({
        //     target: modalController,
        //     parentController: modalController.get('parentController') || modalController,
        //     content: object
        // });

        // Create the sub controller and insert into frontSide of modal unless
        // we are doing the flip transition - if this is a flip then we can
        // only arrive here if we have a controller on the frontSide and nothing
        // on the back.
        var outletName = 'modalFront';

        if (transition == 'flip') {
            outletName = 'modalBack';
        } else {
            outletName = 'modalFront';

            // Push the new modalController onto the stack
            this.get('content').pushObject(modalController);
        }

        // this.render(controllerClass, {
        //     into: ,
        //     outlet: outletName,
        //     controller: newController
        // });

        return modalController;
    },

});

BB.ModalContainerView = Em.View.extend(Ember.TargetActionSupport,{
    tagName: null,

    touchStart: function(event) {
        var _this = this,
            string = event.target.className.substring()
            className = string.indexOf("is-active");

        if (className > 0) {
            _this.get('controller').send('closeModal');
        }
    },

    click: function(e) {
        var _this = this,
            string = e.target.className.substring(),
            className = string.indexOf("is-active");

        if (className > 0) {
            _this.get('controller').send('closeModal');
        }
    },
    
    template: Ember.Handlebars.compile([
        '<div class="modal-fullscreen-background is-active">',
            '{{outlet "currentModal"}}',
        '</div>'].join("\n"))
});

BB.ModalController = Em.ObjectController.extend({
    modals: null,
    frontName: null,
    frontController: null,
    backController: null,

    setController: function (modalSide, controllerClass) {
        // Create the controller to be inserted into the modal
        var contentController = this.container.lookupFactory('controller:' + controllerClass).create();

        this.container.lookup('route:application').render(controllerClass, {
            into: 'modal',
            outlet: modalSide,
            controller: contentController
        });

        this.set('frontController', contentController);
    }
});

BB.ModalView = Em.View.extend(Ember.TargetActionSupport, {
    tagName: null,

    template: Ember.Handlebars.compile([
        '<div {{bindAttr class=":normal :modal-fullscreen-container"}}>',
            '<div id="card">',
                '<div class="front">',
                    '<div class="modal-fullscreen-item">{{outlet "modalFront"}}</div>',
                '</div>',
                '<div class="back">',
                    '<div class="modal-fullscreen-item">{{outlet "modalBack"}}</div>',
                '</div>',
            '</div>',
        '</div>'].join('\n'))
});

