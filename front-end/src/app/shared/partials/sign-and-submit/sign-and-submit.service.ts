import { Injectable } from '@angular/core';
import { ScheduleActions } from 'src/app/forms/form-3x/individual-receipt/schedule-actions.enum';

@Injectable({
  providedIn: 'root'
})
export class SignAndSubmitService {


  private _formTitle: string;
  private _emailsOnFile: any;
  private _reportId: string; 
  private _scheduleAction: ScheduleActions;
  private _formData: any;
  private _treasurerData: any;
  private _formType: any;
  
  public get formTitle(): string {
    return this._formTitle;
  }
  public set formTitle(value: string) {
    this._formTitle = value;
  }
  public get emailsOnFile(): any {
    return this._emailsOnFile;
  }
  public set emailsOnFile(value: any) {
    this._emailsOnFile = value;
  }
  public get reportId(): string {
    return this._reportId;
  }
  public set reportId(value: string) {
    this._reportId = value;
  }
  public get scheduleAction(): ScheduleActions {
    return this._scheduleAction;
  }
  public set scheduleAction(value: ScheduleActions) {
    this._scheduleAction = value;
  }
  public get formData(): any {
    return this._formData;
  }
  public set formData(value: any) {
    this._formData = value;
  }
  public get treasurerData(): any {
    return this._treasurerData;
  }
  public set treasurerData(value: any) {
    this._treasurerData = value;
  }
  public get formType(): any {
    return this._formType;
  }
  public set formType(value: any) {
    this._formType = value;
  }
  
  constructor() { }

  public clearAll(){
    this._formTitle = null;
    this._emailsOnFile = null;
    this._reportId = null; 
    this._scheduleAction = null;
    this._formData = null;
    this._treasurerData = null;
    this._formType = null;
  }
  
}
