#!/bin/bash

CLUSTER="rag-pdf-agent-cluster"
SERVICE="rag-pdf-agent-service"

echo "========================================="
echo "ECS Service Diagnostics"
echo "========================================="

# Get latest task ARN
echo ""
echo "1. Getting latest task ARN..."
TASK_ARN=$(aws ecs list-tasks --cluster $CLUSTER --service-name $SERVICE --query 'taskArns[0]' --output text)

if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
    echo "ERROR: No running tasks found!"
    exit 1
fi
echo "   Task ARN: $TASK_ARN"

# Get task status
echo ""
echo "2. Checking task status..."
TASK_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].lastStatus' --output text)
echo "   Status: $TASK_STATUS"

DESIRED_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].desiredStatus' --output text)
echo "   Desired: $DESIRED_STATUS"

# Get container status
echo ""
echo "3. Checking container status..."
CONTAINER_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].containers[0].lastStatus' --output text)
echo "   Container Status: $CONTAINER_STATUS"

CONTAINER_REASON=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].containers[0].reason' --output text)
if [ "$CONTAINER_REASON" != "None" ] && [ -n "$CONTAINER_REASON" ]; then
    echo "   Container Reason: $CONTAINER_REASON"
fi

STOP_REASON=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].stoppedReason' --output text)
if [ "$STOP_REASON" != "None" ] && [ -n "$STOP_REASON" ]; then
    echo "   Stop Reason: $STOP_REASON"
fi

# Get health status
echo ""
echo "4. Checking health status..."
HEALTH_STATUS=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].containers[0].healthStatus' --output text)
echo "   Health: $HEALTH_STATUS"

# Get ENI and network info
echo ""
echo "5. Getting network info..."
ENI_ID=$(aws ecs describe-tasks --cluster $CLUSTER --tasks "$TASK_ARN" --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

if [ -z "$ENI_ID" ] || [ "$ENI_ID" == "None" ]; then
    echo "   ERROR: Could not get ENI ID"
else
    echo "   ENI ID: $ENI_ID"

    PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
    echo "   Public IP: $PUBLIC_IP"

    SG_ID=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" --query 'NetworkInterfaces[0].Groups[0].GroupId' --output text)
    echo "   Security Group: $SG_ID"

    # Check if port 8000 is open
    echo ""
    echo "6. Checking security group rules for port 8000..."
    PORT_OPEN=$(aws ec2 describe-security-groups --group-ids "$SG_ID" --query "SecurityGroups[0].IpPermissions[?FromPort==\`8000\`]" --output text)

    if [ -z "$PORT_OPEN" ]; then
        echo "   Port 8000 is NOT open. Opening it now..."
        aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 8000 --cidr 0.0.0.0/0 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "   Port 8000 opened successfully!"
        else
            echo "   Port 8000 may already be open or there was an error"
        fi
    else
        echo "   Port 8000 is open"
    fi
fi

# Get recent logs
echo ""
echo "7. Recent container logs..."
TASK_ID=$(echo $TASK_ARN | awk -F'/' '{print $NF}')
LOG_STREAM="ecs/rag-pdf-agent/$TASK_ID"

aws logs get-log-events --log-group-name /ecs/rag-pdf-agent --log-stream-name "$LOG_STREAM" --limit 20 --query 'events[*].message' --output text 2>/dev/null

if [ $? -ne 0 ]; then
    echo "   Could not fetch logs. Log stream may not exist yet."
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
if [ "$TASK_STATUS" == "RUNNING" ] && [ -n "$PUBLIC_IP" ]; then
    echo "App URL: http://$PUBLIC_IP:8000"
    echo ""
    echo "If still not loading, check:"
    echo "  - Container logs above for errors"
    echo "  - Health status: $HEALTH_STATUS"
else
    echo "Task is not running properly."
    echo "Status: $TASK_STATUS"
    echo "Check the logs and reasons above."
fi
