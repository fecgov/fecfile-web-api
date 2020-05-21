/**
 * Components extending the AbstractSchedule base class should
 * each have an enumeration for determining the parent class at runtime.
 * Note: The schedMainComponent supports
 * several schedules A, B, D, H4 and H6.
 */
/**
 * Components extending the AbstractSchedule base class should
 * each have an enumeration for determining the parent class at runtime.
 * Note: The schedMainComponent supports
 * several schedules A, B, D, H4 and H6.
 */
export enum AbstractScheduleParentEnum {
  schedMainComponent = 'schedMainComponent',
  schedFComponent = 'schedFComponent',
  schedFCoreComponent = 'schedFCoreComponent',
  schedH2Component = 'schedH2Component',
  schedH3Component = 'schedH3Component',
  schedH4Component = 'schedH4Component',
  schedH5Component = 'schedH5Component',
  schedLComponent = 'schedLComponent',
  schedEComponent = 'schedEComponent'
}
