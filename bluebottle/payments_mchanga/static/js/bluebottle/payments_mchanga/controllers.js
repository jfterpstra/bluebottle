App.MchangaMpesaController = App.StandardPaymentMethodController.extend({
    requiredFields: ['mpesa_confirmation'],

    init: function() {
        this._super();
        this.set('model', App.MchangaMpesa.create());
    }

});

App.MchangaAirtelController = App.StandardPaymentMethodController.extend({
    requiredFields: ['airtel_code'],

    init: function () {
        this._super();
        this.set('model', App.MchangaMpesa.create());
    }
});
