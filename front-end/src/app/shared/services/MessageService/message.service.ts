import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subject } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class MessageService {

    private _subject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _populateChildComponentsubject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _rollbackChangesSubject: BehaviorSubject<any> = new BehaviorSubject<any>('');
    private _updateReportType: BehaviorSubject<any> = new BehaviorSubject<any>('');

    constructor() { }

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendMessage(message: any) {
        this._subject.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearMessage() {
        this._subject.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getMessage(): Observable<any> {
        return this._subject.asObservable();
    }

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendPopulateChildComponentMessage(message: any) {
        this._populateChildComponentsubject.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearPopulateChildComponentMessage() {
        this._populateChildComponentsubject.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getPopulateChildComponentMessage(): Observable<any> {
        return this._populateChildComponentsubject.asObservable();
    }

    /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendRollbackChangesMessage(message: any) {
        this._rollbackChangesSubject.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearRollbackChangesMessage() {
        this._rollbackChangesSubject.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getRollbackChangesMessage(): Observable<any> {
        return this._rollbackChangesSubject.asObservable();
    }

        /**
     * Sends the message to a component.
     *
     * @param      {Any}  message  The message
     */
    public sendUpdateReportTypeMessage(message: any) {
        this._updateReportType.next(message);
    }

    /**
     * Clears the message if needed.
     *
     */
    public clearUpdateReportTypeMessage() {
        this._updateReportType.next('');
    }

    /**
     * Gets the message.
     *
     * @return     {Observable}  The message.
     */
    public getUpdateReportTypeMessage(): Observable<any> {
        return this._updateReportType.asObservable();
    }

}
