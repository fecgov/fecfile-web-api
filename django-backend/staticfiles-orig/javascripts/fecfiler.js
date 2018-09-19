(function () {
    'use strict';

    angular
        .module('fecfiler', [
            'fecfiler.config',
            'fecfiler.routes',
            'fecfiler.authentication',
            'fecfiler.layout',
            'fecfiler.posts',
            'fecfiler.utils',
            'fecfiler.profiles'
        ]);

    angular
        .module('fecfiler.config', []);

    angular
        .module('fecfiler.routes', ['ngRoute']);

    angular
        .module('fecfiler')
        .run(run);

    run.$inject = ['$http'];

    /**
     * @name run
     * @desc Update xsrf $http headers to align with Django's defaults
     */
    function run($http) {
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';
        $http.defaults.xsrfCookieName = 'csrftoken';
    }
})();