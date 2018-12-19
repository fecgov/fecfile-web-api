import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { form99 } from '../../interfaces/FormsService/FormsService';
import { environment } from '../../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FormsService {

  constructor(
    private _http: HttpClient,
    private _cookieService: CookieService
  ) { }

  /**
   * Gets the form.
   *
   * @param      {String}   committee_id  The committee identifier.
   * @param      {boolean}  is_submitted  Indicates if submitted.
   * @param      {String}   form_type     The form type.
   *
   * @return     {Observable} The form being retreived.
   */
  public getForm(committee_id: string, is_submitted: boolean, form_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let params = new HttpParams();
    let url: string = '';

    if(form_type === '99') {
      url = '/f99/fetch_f99_info';
    }

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    params = params.append('committeeid', committee_id);
    params = params.append('is_submitted', is_submitted.toString());

    return this._http
     .get(
        `${environment.apiUrl}${url}`,
        {
          headers: httpOptions,
          params
        }
      );
  }

  /**
   * Validates a form
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable}  The validation results of the form.
   */
  public validateForm(formObj: any, form_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let httpOptions =  new HttpHeaders();
    let url: string = '';
    let data: any = {};
   
    
    
    
    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));

      url = '/f99/validate_f99';

      data = form99_details;

      data.text = data.text.replace(/<[^>]*>/g, '');

      data.text = data.text.replace(/(&nbsp;)/g, ' ');
    }

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    return this._http
      .post<form99>(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            return true;
          }
          return false;
      }));

  }

  /**
   * Saves a form.
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable} The result of the form being saved.
   */
  /*public saveForm(formObj: any, form_type: string): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let data: any = {};
    let httpOptions =  new HttpHeaders();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem(`form_${form_type}_details`));

      if(localStorage.getItem(`form_${form_type}_saved`) !== null) {
        let formSavedObj = JSON.parse(localStorage.getItem(`form_${form_type}_saved`));
        let formStatus: boolean = formSavedObj.saved;

        if(formStatus) {
          url = '/f99/update_f99_info'; 
        } else {
          url = '/f99/create_f99_info';
        } 
      } else {
        url = '/f99/create_f99_info';  
      }
      
      data = form99_details;

      data['form_type'] = 'F99';
    }

    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if(res) {
            return res;
          }
          return false;
      }));

  }*/

  public saveForm(formObj: any, file: any, form_type: string): Observable<any> {
    console.log('saveForm: ');
    console.log('formObj: ', formObj);
    let form_99_details_res: any ={};
    let form_99_details_res_tmp: form99;

    let token: string = JSON.parse(this._cookieService.get('user'));
    let data: any = {};
    let formData: FormData = new FormData();
    let httpOptions =  new HttpHeaders();
    let url: string = '';
    let id:string;

    if(file && file.name) {
      console.log('file: ', file);
      httpOptions = httpOptions.append('enctype', 'multipart/form-data');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);    
    } else {
      /*httpOptions = httpOptions.append('Content-Type', 'application/json');*/
      httpOptions = httpOptions.append('enctype', 'multipart/form-data');
      httpOptions = httpOptions.append('Authorization', 'JWT ' + token);
    }

    console.log('form_type',form_type);

    if(form_type === '99') {

      let form99_details: form99 = JSON.parse(localStorage.getItem(`form_${form_type}_details`));
     
      /*if (form99_details.id===null || form99_details.id===''){
        form99_details.id="0";
        localStorage.setItem('id', "0");
      }*/

      console.log ('form99_details: ',form99_details);

      if(file && file.name) {
        console.log ('file uploaded successfully');
        localStorage.setItem('form_99_details.file', file);
        formData.append('file', file, file.name);         
        formData.append('committeeid', form99_details.committeeid);
        formData.append('committeename', form99_details.committeename);
        formData.append('street1', form99_details.street1);
        formData.append('street2', form99_details.street2);
        formData.append('city', form99_details.city);
        formData.append('state', form99_details.state);
        formData.append('zipcode', form99_details.zipcode);
        formData.append('treasurerprefix', form99_details.treasurerprefix);
        formData.append('treasurerfirstname', form99_details.treasurerfirstname);
        formData.append('treasurermiddlename', form99_details.treasurermiddlename);
        formData.append('treasurerlastname', form99_details.treasurerlastname);
        formData.append('treasurersuffix', form99_details.treasurersuffix);
        formData.append('reason', form99_details.reason);
        formData.append('text', form99_details.text);
        formData.append('signee', form99_details.signee);
        formData.append('email_on_file', form99_details.email_on_file);
        formData.append('email_on_file_1', form99_details.email_on_file_1);
        formData.append('additional_email_1', form99_details.additional_email_1);
        formData.append('additional_email_2', form99_details.additional_email_2);        
        formData.append('created_at', form99_details.created_at);
        formData.append('is_submitted', "False");
        formData.append('filename', form99_details.filename);
        formData.append('form_type', "F99");
        if (form99_details.id.toString() ==='' || form99_details.id.toString() ==="" || form99_details.id===null){
        
          /*data['id']="0";*/
          formData.append('id', "0");
        }
        else
        {
          formData.append('id', form99_details.id.toString());
        }
      }
      else
      {
        /*form99_details.is_submitted=false; */
        formData.append('file', form99_details.file);  
        formData.append('filename', form99_details.filename);    
        formData.append('committeeid', form99_details.committeeid);
        formData.append('committeename', form99_details.committeename);
        formData.append('street1', form99_details.street1);
        formData.append('street2', form99_details.street2);
        formData.append('city', form99_details.city);
        formData.append('state', form99_details.state);
        formData.append('zipcode', form99_details.zipcode);
        formData.append('treasurerprefix', form99_details.treasurerprefix);
        formData.append('treasurerfirstname', form99_details.treasurerfirstname);
        formData.append('treasurermiddlename', form99_details.treasurermiddlename);
        formData.append('treasurerlastname', form99_details.treasurerlastname);
        formData.append('treasurersuffix', form99_details.treasurersuffix);
        formData.append('reason', form99_details.reason);
        formData.append('text', form99_details.text);
        formData.append('signee', form99_details.signee);
        formData.append('email_on_file', form99_details.email_on_file);
        formData.append('email_on_file_1', form99_details.email_on_file_1);
        formData.append('additional_email_1', form99_details.additional_email_1);
        formData.append('additional_email_2', form99_details.additional_email_2);        
        formData.append('created_at', form99_details.created_at);
        formData.append('is_submitted', "False");
        /*formData.append('filename', form99_details.filename);*/
        formData.append('form_type', "F99");
        if (form99_details.id.toString() ==='' || form99_details.id.toString() ==="" || form99_details.id===null){
        
          /*data['id']="0";*/
          formData.append('id', "0");
        }
        else
        {
          formData.append('id', form99_details.id.toString());
        }

      }  
      

      if(localStorage.getItem(`form_${form_type}_saved`) !== null) {
        let formSavedObj = JSON.parse(localStorage.getItem(`form_${form_type}_saved`));
        let formStatus: boolean = formSavedObj.saved;

        if(formStatus) {
          url = '/f99/create_f99_info'; 
        } else {
          url = '/f99/create_f99_info';
        } 
      } else {
        url = '/f99/create_f99_info';  
      }
      
      /*data = form99_details;
      form99_details.form_type="F99";
      data = (file) ? formData : form99_details;*/
      data=formData;

      /*if (form99_details.id.toString() ==='' || form99_details.id.toString() ==="" || form99_details.id===null){
        
        data['id']="0";
      }
      else
      {
        data['id']= form99_details.id;
      }

      data['form_type'] = 'F99';*/
      /*data['filename'] = '';*/
    }

    console.log ('Dupdated Data: ',data);

    console.log ('loop through simple form Data: ');

    for (var value of data.values()) {
      console.log(value); 
   }
    console.log ('loop through form Data: ');
    console.log(data);

    /*for(let pair of data.entries()) {
      console.log(pair[0] + ": ", pair[1]); 
   }*/

   new Response(data).text().then(console.log)
    
    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            localStorage.setItem('form_99_details_res', JSON.stringify(res));
            let form99_details_res: form99 = JSON.parse(localStorage.getItem(`form_99_details_res`));
            id=form99_details_res.id.toString();
            /*form_99_details_res_tmp.id=form_99_details_res.id; //just to get form 99 id
            localStorage.setItem('id', form_99_details_res_tmp.id);*/
            localStorage.setItem('form_99_details.id', id);

            return res;
          }
          return false;
      }));
}


  /**
   * Submits a form.
   *
   * @param      {Object}  formObj    The form object.
   * @param      {String}  form_type  The form type.
   *
   * @return     {Observable}  The result of submitting a form.
   */
  public submitForm(formObj: any, form_type): Observable<any> {
    let token: string = JSON.parse(this._cookieService.get('user'));
    let data: any = {};
    let httpOptions =  new HttpHeaders();
    let url: string = '';

    httpOptions = httpOptions.append('Content-Type', 'application/json');
    httpOptions = httpOptions.append('Authorization', 'JWT ' + token);

    if(form_type === '99') {
      let form99_details: form99 = JSON.parse(localStorage.getItem('form_99_details'));

      url = '/f99/submit_comm_info';
      data = form99_details;

       data['form_type'] = 'F99';
    }
    return this._http
      .post(
        `${environment.apiUrl}${url}`,
        data,
        {
          headers: httpOptions
        }
      )
      .pipe(map(res => {
          if (res) {
            localStorage.removeItem('form_99_details');
            localStorage.removeItem('form_99_details_res');
            return true;
          }
          return false;
      }));      
  }
}
