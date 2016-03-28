# -*- coding: utf-8 -*-
"""
Visualization tools for showing the results of a pyshield calculation run.

A heatmap is shown on top of the floor plan. Isocontours specified in the
config file are shown as well.

Last Updated 05-02-2016
"""


from matplotlib import pyplot as plt
from pyshield import config, data, log, const
from pyshield.calculations.isotope import equivalent_activity
from os.path import join
from datetime import datetime
import pickle
import numpy as np

SOURCE = 'Source'
SHIELDING = 'Shielding'




def show_floorplan():
  """ Show shielding barriers on top of floor plan. """
  
  floor_plan = data[const.FLOOR_PLAN]
  shielding=data[const.SHIELDING]
  sources=data[const.SOURCES]
  
  def shielding_click(name):
    text = name + ':'
    
    for material, thickness in shielding[name][const.MATERIAL].items():
      text += ' '  + material  + ': ' + str(thickness) + 'cm'
  
    return text
   
  def source_click(name):
    text = 'Isotope: {isotope} \n Equivalent Activity: {activity}'
     
    source = sources[name]
    
    activity = equivalent_activity(source[const.DESINT], source[const.ISOTOPE])
    text = text.format(isotope = source[const.ISOTOPE], activity = str(np.round(activity)) + ' MBq')
    return text
  
  def object_click(event):
    """Show information about line with mouse click on the line """
 
    obj_name = event.artist.name   
  
    if obj_name in shielding.keys():
      text =  shielding_click(obj_name)
    elif obj_name in sources.keys():
      text =  source_click(obj_name)
    else:
      raise
      
    print(text)
    
    text_label.set_text(text)
    event.canvas.draw()
    return True
  
        
  def draw_thickness(barrier):
    """ Barrier thickness weighted by density """
    d=0
    for material, thickness in barrier[const.MATERIAL].items():       
      d += (thickness * data[const.MATERIALS][material][const.DENSITY])
    return d
      
  # show floor plan 
  fig=plt.figure()
  plt.imshow(floor_plan)
  # information text
  text_label = plt.text(0, 0 , 'Select Line')
  
  #plot shielding baririers  
  
  for name, barrier in shielding.items():
     l=barrier[const.LOCATION]
     
     line, = plt.plot( (l[0], l[2]), (l[1], l[3]), 'k-', 
                        linewidth=draw_thickness(barrier)/5, 
                        picker=draw_thickness(barrier)/5)
     
     line.name = name
  
  # enable mouse interaction     
  

  # plot red dot at source locations
  for name, source in sources.items():
      point, = plt.plot(*source[const.LOCATION], 'ro', picker = 5)
      point.name = name
  fig.canvas.mpl_connect('pick_event', object_click)
  return fig
    

def plot_dose_map(floorplan, dose_map=None):
  """ Plot a heatmap with isocontours on top of the floorplan wiht barriers """
  
  isocontours = config[const.ISOCONTOURS]
  clim = config[const.CLIM_HEATMAP]  
  colormap = config[const.COLORMAP]
  
  extent = (0.5, floorplan.shape[1]-0.5, 
            floorplan.shape[0]-0.5, 0.5)
                
  fig=show_floorplan()
  
  # show heatmap
  plt.imshow(dose_map, extent=extent, 
             alpha = 0.5,
             clim=clim,
             cmap=plt.get_cmap(colormap))
  
  # show isocontours
  C=plt.contour(dose_map, isocontours[const.VALUES],
                colors=isocontours[const.COLORS],
                extent=(extent[0], extent[1],extent[3], extent[2]))
  
  # show isocontour value in line  
  plt.clabel(C, inline=1, fontsize=10)
  
  # show legend for isocontours  
  plt.legend(C.collections, [str(value) + ' mSv' for value in config[const.ISOCONTOURS][const.VALUES]])
  return fig


def show(dose_maps = None):
  """ show a dictonary with dosemaps on top of the floor plan and 
      save to disk. """
  figures={}
  

    
  # show and save all figures it config property is set to show all
  if dose_maps is not None:  
    if config[const.SHOW][const.ALL_SOURCES] and config[const.SHOW][const.SUM_SOURCES]:
      keys = dose_maps.keys()
    elif config[const.SHOW][const.SUM_SOURCES]:
      keys = (const.SUM_SOURCES,)
    elif config[const.SHOW][const.ALL_SOURCES]:
      keys = list(dose_maps.keys())
      keys.remove(const.SUM_SOURCES)
  else:

    show_floorplan()
    return
    
    # iterate over dosemaps    
  
  
  
  for key in keys:
    dmap = dose_maps[key]      
    figures[key] = plot_dose_map(data[const.FLOOR_PLAN], dmap)
    figures[key].canvas.set_window_title(key)
    plt.gca().set_title(key)
    maximize_window()
      

      

  return figures
        
      
def save(figures = None, dose_maps = None):
  if not(config[const.EXPORT][const.SAVE_DISPLAYED]):
    log.debug('No figures are displayed')
  elif figures is not None:  
    for name, figure in figures.items():
      save_figure(figure, name.lower())
      
  
  if dose_maps is not None and config[const.EXPORT][const.EXPORT_RAW]:
    fname = config[const.EXPORT][const.EXPORT_RAW_FNAME]
    if '{time_stamp}' in fname:
      time_stamp = datetime.strftime(datetime.now(), '_%Y%m%d-%H%M%S')
      fname = fname.format(time_stamp = time_stamp)
     
    fname = join(config[const.EXPORT][const.EXPORT_DIR], fname)
    log.debug('Pickle dumping data: ' + fname)
    pickle.dump(dose_maps, open(fname, 'wb'))
    log.debug('results dumped to file: ' + fname)
    

          
def maximize_window():
    """ Maximize the current plot window """
    backend = plt.get_backend()
    mng = plt.get_current_fig_manager()
    
    # Maximization depends on matplotlib backend
    if backend == 'Qt4Agg':
      mng.window.showMaximized()
    elif backend == 'wxAgg':
      mng.frame.Maximize(True)
    elif backend == 'TkAgg':
      mng.window.state('zoomed')
    elif backend == 'MacOSX':
      mng.full_screen_toggle()
    else:   
      log.warn('Cannot maximize a pyplot figure that uses ' + backend + ' as backend')
    return
    
    
    
def save_figure(fig, source_name):
  """ save specifed figure to disk, file name gets a time stamp appended"""  
  
  fname = config[const.EXPORT][const.EXPORT_FIG_FNAME]
  if '{time_stamp}' and '{source_name}' in fname:  
    time_stamp = datetime.strftime(datetime.now(), '_%Y%m%d-%H%M%S')
    fname = fname.format(time_stamp = time_stamp, source_name = source_name)
  else:
      log.error('Invalid filename: ' + fname)
  
  fname = join(config[const.EXPORT][const.EXPORT_DIR], fname)
  dpi = config[const.EXPORT][const.DPI]
  log.debug('Writing: ' + fname)
  fig.savefig(fname, dpi=dpi, bbox_inches='tight')
  


 

