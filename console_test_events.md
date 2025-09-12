# AWS Lambda Console Test Events

Copy and paste these test events directly into the AWS Lambda console to test your function.

## Test Event 1: Critical Ball Bearing Fault
**Expected Result:** HIGH risk, immediate action required

```json
{
  "speed": 117.3,
  "load": 512.9,
  "current": 3.21,
  "temperature": 39.59,
  "vibration": 2.85,
  "prediction": "Ball Bearing Fault"
}
```

## Test Event 2: Drive Motor Fault
**Expected Result:** HIGH risk due to electrical safety concerns

```json
{
  "speed": 89.2,
  "load": 678.4,
  "current": 6.78,
  "temperature": 67.3,
  "vibration": 0.45,
  "prediction": "Drive Motor Fault"
}
```

## Test Event 3: Belt Slippage
**Expected Result:** LOW risk, routine maintenance

```json
{
  "speed": 95.1,
  "load": 423.7,
  "current": 2.89,
  "temperature": 32.4,
  "vibration": 0.52,
  "prediction": "Belt Slippage"
}
```

## Test Event 4: Central Shaft Fault
**Expected Result:** HIGH risk, immediate shutdown recommended

```json
{
  "speed": 45.8,
  "load": 892.1,
  "current": 4.56,
  "temperature": 78.9,
  "vibration": 3.21,
  "prediction": "Central Shaft Fault"
}
```

## Test Event 5: Normal Operation
**Expected Result:** LOW risk, continue monitoring

```json
{
  "speed": 125.6,
  "load": 456.2,
  "current": 3.45,
  "temperature": 28.7,
  "vibration": 0.34,
  "prediction": "Normal Operation"
}
```

## Test Event 6: Pulley Fault
**Expected Result:** MEDIUM risk, schedule maintenance

```json
{
  "speed": 102.4,
  "load": 567.8,
  "current": 3.78,
  "temperature": 45.2,
  "vibration": 1.23,
  "prediction": "Pulley Fault"
}
```

## Test Event 7: Idler Roller Fault
**Expected Result:** MEDIUM risk, monitor closely

```json
{
  "speed": 134.7,
  "load": 389.5,
  "current": 2.98,
  "temperature": 41.6,
  "vibration": 1.67,
  "prediction": "Idler Roller Fault"
}
```

---

## How to Test in AWS Lambda Console:

1. **Go to AWS Lambda Console**
2. **Select your function**
3. **Click "Test" tab**
4. **Create new test event**
5. **Copy-paste one of the JSON events above**
6. **Click "Test"**

## Expected S3 Output Location:
```
s3://relu-quicksight/bedrock-recommendations/analytics/YYYY/MM/DD/
s3://relu-quicksight/bedrock-recommendations/detailed/YYYY/MM/DD/HH/
```

## What to Check After Testing:

1. **Lambda Response:** Should return 200 status with S3 location
2. **CloudWatch Logs:** Check for any errors or processing details
3. **S3 Bucket:** Verify files are created in `relu-quicksight` bucket
4. **File Content:** Check both analytics and detailed JSON files

## Sample Expected Response:
```json
{
  "statusCode": 200,
  "body": {
    "message": "Successfully processed inference and generated recommendation",
    "s3_location": "s3://relu-quicksight/bedrock-recommendations/detailed/2025/09/11/14/detailed_20250911_143052_123456.json",
    "recommendation_summary": "Ball bearing failure detected with high confidence..."
  }
}
```