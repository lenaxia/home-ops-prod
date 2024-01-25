  language: "en",
  //locale: "en-US",
  address: "0.0.0.0",
  port: 8080,
  ipWhitelist: ["127.0.0.1", "10.43.0.0/16", "192.168.0.0/16"],
  logLevel: ["INFO", "LOG", "WARN", "ERROR"], // Add "DEBUG" for even more logging
  timeFormat: 24,
  units: "metric",
  modules: [
    {
      module: "alert",
    },
    {
      module: "updatenotification",
      position: "top_bar"
    },
    {
      module: "clock",
      position: "top_left"
    },
    {
      module: "calendar",
      header: "US Holidays",
      position: "top_left",
      config: {
        calendars: [
          {
            symbol: "calendar-check",
            url: "webcal://www.calendarlabs.com/ical-calendar/ics/76/US_Holidays.ics"					}
        ]
      }
    },
    {
      module: "compliments",
      position: "lower_third"
    },
    {
      module: "weather",
      position: "top_right",
      config: {
        weatherProvider: "openweathermap",
        type: "current",
        location: "New York",
        locationID: "5128581", //ID from http://bulk.openweathermap.org/sample/city.list.json.gz; unzip the gz file and find your city
        apiKey: "YOUR_OPENWEATHER_API_KEY"
      }
    },
    {
      module: "weather",
      position: "top_right",
      header: "Weather Forecast",
      config: {
        weatherProvider: "openweathermap",
        type: "forecast",
        location: "New York",
        locationID: "5128581", //ID from http://bulk.openweathermap.org/sample/city.list.json.gz; unzip the gz file and find your city
        apiKey: "YOUR_OPENWEATHER_API_KEY"
      }
    },
    {
      module: "newsfeed",
      position: "bottom_bar",
      config: {
        feeds: [
          {
            title: "New York Times",
            url: "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"
          }
        ],
        showSourceTitle: true,
        showPublishDate: true,
        broadcastNewsFeeds: true,
        broadcastNewsUpdates: true
      }
    },
  ]


