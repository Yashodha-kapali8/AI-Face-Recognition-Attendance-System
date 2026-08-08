from django.db import models
from django.utils import timezone


class Student(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    phone_number = models.CharField(max_length=15)
    student_class = models.CharField(max_length=100)
    image = models.ImageField(upload_to='students/')
    authorized = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    PERIOD_CHOICES = [
        ('1', 'Period 1'),
        ('2', 'Period 2'),
        ('3', 'Period 3'),
        ('4', 'Period 4'),
        ('5', 'Period 5'),
        ('6', 'Period 6'),
        ('7', 'Period 7'),
        ('8', 'Period 8'),
       
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    period = models.CharField(max_length=2, choices=PERIOD_CHOICES)  # Updated for 10 periods
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'date', 'period')  # Ensure one attendance per student per period per day

    def __str__(self):
        return f"{self.student.name} - {self.date} - Period {self.period}"

    def mark_checked_in(self):
        self.check_in_time = timezone.now()
        self.save()

    def mark_checked_out(self):
        if self.check_in_time:
            self.check_out_time = timezone.now()
            self.save()
        else:
            raise ValueError("Cannot mark check-out without check-in.")

    def calculate_duration(self):
        if self.check_in_time and self.check_out_time:
            duration = self.check_out_time - self.check_in_time
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        return None

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.date = timezone.now().date()
        super().save(*args, **kwargs)
