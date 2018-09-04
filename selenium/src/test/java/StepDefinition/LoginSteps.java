package StepDefinition;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.remote.CapabilityType;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.openqa.selenium.support.ui.ExpectedCondition;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import com.karsun.kic.tan.duke.util.ActionByLocator;
import com.paulhammant.ngwebdriver.NgWebDriver;

import cucumber.api.java.en.Given;		
import cucumber.api.java.en.Then;		
import cucumber.api.java.en.When;	
import cucumber.api.java.en.And;
import cucumber.api.java.en.But;


public class LoginSteps {

	private ChromeOptions options;
	private WebDriver driver;
	
	
	@Given("^User clicks on a FEC link on FEC.Gov$")
	public void open_the_Chrome_and_launch_the_application() throws Throwable {
		System.out.println("This Step open the Chrome and launch the application.");

		options = new ChromeOptions();
		options.addArguments("--test-type");
		options.addArguments("--disable-extensions");
		options.addArguments("start-maximized");
		options.addArguments("disable-infobars");
		System.setProperty("webdriver.chrome.driver", "C:\\FEC\\Selenium\\chromedriver_win32\\chromedriver.exe");
		driver = new ChromeDriver(options);
		driver.manage().timeouts().implicitlyWait(120, TimeUnit.SECONDS);
		driver.manage().window().maximize();
		driver.get("https://www.fec.gov/help-candidates-and-committees/filing-reports/fecfile-software/");
		
	}
	
	@Then("^FEC file login page is launched$")
	public void click_on_fecfile() throws Throwable {
		driver.findElement(By.xpath("//a[@class='button--cta button--export']")).click();
	
		
	}	
		
}
