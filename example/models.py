from django.db import models
from django.core.urlresolvers import reverse

class Page(models.Model):
    class Meta:
        ordering = ['id']

    slug = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    text = models.TextField()
    parent = models.ForeignKey('self', related_name='children', null=True, blank=True)

    def get_absolute_url(self):
        return reverse('page', kwargs={'slug': self.slug})
    
    def __unicode__(self):
        return self.slug

    def get_ancestors(self):
        ancestors = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = parent.parent
        return self.__class__.objects.filter(id__in=[ancestor.id for ancestor in ancestors])
# Or use:
#mptt.register(Page)

class Catalog(models.Model):
    class Meta:
        ordering = ['id']

    title = models.CharField(max_length=100)
    parent = models.ForeignKey('self', related_name='children', null=True, blank=True)
    visible = models.BooleanField()

    def get_absolute_url(self):
        return reverse('catalog', kwargs={'object_id': self.pk})

    def __unicode__(self):
        return unicode(self.pk)

    def get_ancestors(self):
        ancestors = []
        parent = self.parent
        while parent is not None:
            ancestors.append(parent)
            parent = parent.parent
        return self.__class__.objects.filter(id__in=[ancestor.id for ancestor in ancestors])
# Or use:
#mptt.register(Page)


class News(models.Model):
    class Meta:
        ordering = ['id']

    text = models.TextField()
    
    def title(self):
        return self.text

    def get_absolute_url(self):
        return reverse('news', kwargs={'object_id': self.pk})

    def __unicode__(self):
        return unicode(self.pk)
