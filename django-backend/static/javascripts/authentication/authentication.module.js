(function () {
    'use strict';

    angular
        .module('fecfiler.authentication', [
            'fecfiler.authentication.controllers',
            'fecfiler.authentication.services'
        ]);

    angular
        .module('fecfiler.authentication.controllers', []);

    angular
        .module('fecfiler.authentication.services', ['ngCookies']);
})();