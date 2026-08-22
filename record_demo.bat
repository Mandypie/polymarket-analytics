@echo off
echo ================================================
echo Polymarket Analytics - Screen Recording Helper
echo ================================================
echo.
echo This will help you record a screen demo of the app.
echo.
echo METHOD 1 - Windows Built-in (Recommended):
echo 1. Make sure the demo is visible in Chrome (http://localhost:8502)
echo 2. Press Win + G to open Game Bar
echo 3. Click the Record button
echo 4. Record your walkthrough
echo 5. Press Win + Shift + R to stop recording
echo 6. Video saves to: Videos\Captures folder
echo.
echo METHOD 2 - PowerPoint:
echo 1. Open PowerPoint
echo 2. Insert -^> Screen Recording
echo 3. Select the Chrome window
echo 4. Record and save
echo.
echo ================================================
echo.
echo Opening Chrome demo now...
echo.
start chrome "http://localhost:8502"
timeout /t 3 /nobreak
echo Demo is open in Chrome. Use Win+G to start recording!
pause