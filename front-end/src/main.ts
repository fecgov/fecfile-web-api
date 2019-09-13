import { enableProdMode } from '@angular/core';
import { platformBrowserDynamic } from '@angular/platform-browser-dynamic';

import { AppModule } from './app/app.module';
import { environment } from './environments/environment';

if (environment.production) {
  enableProdMode();
}

platformBrowserDynamic().bootstrapModule(AppModule)
  .catch(err => console.log(err));

document.write('<script type="text/javascript"> (function() { var s = document.createElement("script"); s.type = "text/javascript"; s.async = true; s.src = \'//api.usersnap.com/load/55f4a866-178e-4cf4-b4b4-58457fdca2bd.js\'; var x = document.getElementsByTagName(\'script\')[0]; x.parentNode.insertBefore(s, x); })(); </script>')