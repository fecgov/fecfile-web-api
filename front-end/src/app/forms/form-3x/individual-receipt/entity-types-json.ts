export const entityTypes = [
  {
    entityType: 'IND',
    entityTypeDescription: 'Individual',
    group: 'ind-group',
    selected: false
  },
  {
    entityType: 'ORG',
    entityTypeDescription: 'Organization',
    group: 'org-group',
    selected: true
  }
];

export const committeeEventTypes = {
  committeeTypeEvents: [
    {
      committeeTypeCategory: 'PAC',
      eventTypes: [
        {
          eventType: 'AD',
          eventTypeDescription: 'Administrative',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        },
        {
          eventType: 'GV',
          eventTypeDescription: 'Generic Voter Drive',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        },
        {
          eventType: 'PC',
          eventTypeDescription: 'Public Communications Referring Only to Party (made by PAC)',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        }
      ]
    },
    {
      committeeTypeCategory: 'PTY',
      eventTypes: [
        {
          eventType: 'AD',
          eventTypeDescription: 'Administrative',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        },
        {
          eventType: 'GV',
          eventTypeDescription: 'Generic Voter Drive',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        },
        {
          eventType: 'EA',
          eventTypeDescription: 'Exempt Activities',
          scheduleType: 'sched_h1',
          activityEventTypes: null
        },
        {
          eventType: 'DF',
          eventTypeDescription: 'Direct Fundraising',
          scheduleType: 'sched_h2',
          activityEventTypes: [
            {
              activityEventType: '??',
              activityEventDescription: "Chicago Men's Club Rotary"
            },
            {
              activityEventType: '??',
              activityEventDescription: 'Nassau Rally'
            }
          ]
        },
        {
          eventType: 'DC',
          eventTypeDescription: 'Direct Candidate Support',
          scheduleType: 'sched_h2',
          activityEventTypes: [
            {
              activityEventType: '??',
              activityEventDescription: "Chicago Men's Club Rotary"
            },
            {
              activityEventType: '??',
              activityEventDescription: 'Nassau Rally'
            }
          ]
        }
      ]
    }
  ]
};
