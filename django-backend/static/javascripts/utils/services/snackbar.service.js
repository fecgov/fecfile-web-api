/**
* Snackbar
* @namespace fecfiler.utils.services
*/
(function ($, _) {
  'use strict';

  angular
    .module('fecfiler.utils.services')
    .factory('Snackbar', Snackbar);

  /**
  * @namespace Snackbar
  */
  function Snackbar() {
    /**
    * @name Snackbar
    * @desc The factory to be returned
    */
    var Snackbar = {
      error: error,
      show: show
    };

    return Snackbar;

    ////////////////////

    /**
    * @name _snackbar
    * @desc Display a snackbar
    * @param {string} content The content of the snackbar
    * @param {Object} options Options for displaying the snackbar
    */
    function _snackbar(content, options) {
      options = _.extend({ timeout: 3000 }, options);
      options.content = content;

      $.snackbar(options);
    }


    /**
    * @name error
    * @desc Display an error snackbar
    * @param {string} content The content of the snackbar
    * @param {Object} options Options for displaying the snackbar
    * @memberOf fecfiler.utils.services.Snackbar
    */
    function error(content, options) {
      if (typeof content === 'string') {
        _snackbar('Error: ' + content, options);
      } else {
        if (content.error) {
          _snackbar('Error: ' + content.error);
        } else if (content.data.error) {
          _snackbar('Error: ' + content.data.error);
        } else if (content.detail) {
          _snackbar('Error: ' + content.detail);
        } else if (content.data.detail) {
          _snackbar('Error: ' + content.data.detail);
        } else if (content.status == 500) {
          _snackbar("Unexpected error. Contact the Administrator.");
        } else if (content.status && content.status == 400 && content.data) {
          //TODO each field error should be displayed below its input box
          var msg = "Errors: <br/>";
          for(var k in content.data) {
            msg += "&bull; <strong>" + k + "</strong>: " + content.data[k].join(". ") + "<br/>";
          }
          if (msg) {
            _snackbar(msg);
          }
        }
      }
    }


    /**
    * @name show
    * @desc Display a standard snackbar
    * @param {string} content The content of the snackbar
    * @param {Object} options Options for displaying the snackbar
    * @memberOf fecfiler.utils.services.Snackbar
    */
    function show(content, options) {
      _snackbar(content, options);
    }
  }
})($, _);