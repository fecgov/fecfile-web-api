/**
 * LoginController
 * @namespace fecfiler.authentication.controllers
 */
(function () {
    'use static';

    angular
        .module('fecfiler.authentication.controllers')
        .controller('LoginController', ['$location', '$scope', 'Authentication', LoginController]);

    /**
     * @namespace LoginController
     */
    function LoginController($location, $scope, Authentication) {

        /**
         * @name login
         * @desc Log the user in
         * @memberOf fecfiler.authentication.controllers.LoginController
         */
        this.login = function() {
            var p = Authentication.login(this.username, this.password);
            p.then(function(value) {
                if (value.status < 200 || value.status >299) {
                    $scope.error = value.data.message;
                }
            }, function(reason) {
                console.log("Error: " + JSON.stringify(reason));
            });
        }
    }
})();
