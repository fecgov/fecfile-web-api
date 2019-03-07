import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Subject } from 'rxjs/Subject';

/**
 * A message service for sending and receiving messages of any type
 * between transaction components.
 */
@Injectable({
  providedIn: 'root'
})
export class TransactionsMessageService {

  private subject = new Subject<any>();
  private applyFiltersSubject = new Subject<any>();

  public sendMessage(message: any) {
    this.subject.next(message);
  }

  public clearMessage() {
    this.subject.next();
  }

  public getMessage(): Observable<any> {
    return this.subject.asObservable();
  }

  public sendApplyFiltersMessage(message: any) {
    this.applyFiltersSubject.next(message);
  }

  public clearApplyFiltersMessage() {
    this.applyFiltersSubject.next();
  }

  public getApplyFiltersMessage(): Observable<any> {
    return this.applyFiltersSubject.asObservable();
  }  
}
