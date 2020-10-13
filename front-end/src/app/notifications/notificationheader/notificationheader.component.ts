import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormsService } from '../../shared/services/FormsService/forms.service';
import { ActivatedRoute } from '@angular/router';
import { Subscription } from 'rxjs/Subscription';
import { NotificationsService } from '../notifications.service';
import { TabConfiguration } from '../notification';

@Component({
  selector: 'app-notificationheader',
  templateUrl: './notificationheader.component.html',
  styleUrls: ['./notificationheader.component.scss'],
  encapsulation: ViewEncapsulation.None
})

export class NotificationheaderComponent implements OnInit {
  public viewMode = '';
  public viewTabs: TabConfiguration[] = [
    {
      id: 1, name: "Prior Notices", count: 0, showOptionView: false, placeholder: true,
      toolTip: "Prior Notices - Sent by the FEC to remind a filer of upcoming reports that may need to be filed based upon the committee type and filing frequency."
    },
    {
      id: 2, name: "Reminder Emails", count: 0, showOptionView: true, placeholder: false,
      toolTip: "Reminder Emails - Sent by the FEC to remind a filer of their next report that is due.  The reminder email is typically sent 2 to 3 business days prior to the official filing deadline."
    },
    {
      id: 3, name: "Late Notification Emails", count: 0, showOptionView: true, placeholder: false,
      toolTip: "Late Notification Emails - Sent by the FEC to remind the filer the day after a filing deadline if the FEC has not yet received the report that was due."
    },
    {
      id: 4, name: "Filing Confirmations", count: 0, showOptionView: false, placeholder: false,
      toolTip: "Filing Confirmations - Emails sent by the FEC within a few minutes of a filer successfully submitting an electronic filing.  This email will include a confirmation number for the successful submission."
    },
    {
      id: 5, name: "RFAIs", count: 0, showOptionView: false, placeholder: true,
      toolTip: "RFAIs - There are letters sent by the Reports Analysis Division when a report or document filed with the FEC needs additional clarification or identifies an error, omission or possible prohibited activity."
    },
    {
      id: 6, name: "Imported Transactions", count: 0, showOptionView: false, placeholder: false,
      toolTip: "Import Transactions - Here you will find transaction documents that have been imported into the system."
    }
  ];
  private activeRoutesSubscription: Subscription;

  constructor(
    private _notificationsService: NotificationsService,
    private _formService: FormsService,
    private _activeRoute: ActivatedRoute
  ) {
  }

  ngOnInit() {
    this.viewMode = 'tab-1';

    if (localStorage.getItem('form3XNotificationInfo.showDashBoard') === "Y") {
      this._formService.removeFormDashBoard("3X");

    }

    this.activeRoutesSubscription = this._activeRoute
      .params
      .subscribe(params => {
      });

    this._notificationsService
      .getNotificationCounts(
      )
      .subscribe((response: {groupName: string, count: number}[]) => {
        if (response) {
          for (let tab of this.viewTabs) {
            var group = response.find( function( item ){
              return item.groupName === tab.name;
            } );
            tab.count = (group != null) ? group.count : 0;
          }
        }
      });
  }

  /**
   * A method to run when component is destroyed.
   */
  public ngOnDestroy(): void {
    this.activeRoutesSubscription.unsubscribe();
  }
}
