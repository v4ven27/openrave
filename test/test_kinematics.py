# -*- coding: utf-8 -*-
# Copyright (C) 2011 Rosen Diankov <rosen.diankov@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from common_test_openrave import *

class TestKinematics(EnvironmentSetup):
    def test_bodybasic(self):
        self.log.info('check if the joint-link set-get functions are consistent along with jacobians')
        env=self.env
        with env:
            for envfile in g_envfiles+['testdata/bobcat.robot.xml']:
                env.Reset()
                self.LoadEnv(envfile,{'skipgeometry':'1'})
                for i in range(20):
                    T = eye(4)
                    for body in env.GetBodies():
                        # change the staticness of the first link (shouldn't affect anything)
                        body.GetLinks()[0].SetStatic((i%2)>0)

                        lowerlimit,upperlimit = body.GetDOFLimits()
                        body.SetDOFValues(lowerlimit)
                        dofvalues = body.GetDOFValues()
                        assert( transdist(lowerlimit,body.GetDOFValues()) <= g_epsilon*len(dofvalues))
                        body.SetDOFValues(upperlimit)
                        dofvalues = body.GetDOFValues()
                        assert( transdist(upperlimit,body.GetDOFValues()) <= g_epsilon*len(dofvalues))
                        
                        Told = body.GetTransform()
                        Tallold,dofbranchesold = body.GetLinkTransformations(True)
                        dofvaluesold = body.GetDOFValues()
                        T = randtrans()
                        body.SetTransform(T)
                        _T = body.GetTransform()
                        assert( transdist(T,_T) <= g_epsilon )
                        body.SetLinkTransformations(Tallold,dofbranchesold)
                        _Tallold,_dofbranchesold = body.GetLinkTransformations(True)
                        assert( transdist(Tallold,_Tallold) <= g_epsilon*len(Tallold) )
                        assert( transdist(dofbranchesold,_dofbranchesold) == 0 )
                        Tallnew = [randtrans() for j in range(len(Tallold))]
                        body.SetLinkTransformations(Tallnew,zeros(body.GetDOF()))
                        _Tallnew,_dofbranchesnew = body.GetLinkTransformations(True)
                        assert( transdist(Tallnew,_Tallnew) <= g_epsilon*len(Tallnew) )
                        for link, T in izip(body.GetLinks(),Tallold):
                            link.SetTransform(T)
                        _Tallold,_dofbranchesold = body.GetLinkTransformations(True)
                        assert( transdist(Tallold,_Tallold) <= g_epsilon*len(Tallold) )
                        # dof
                        # cannot compre dofvaluesold, and _dofvaluesold since branches are not set!
                        #assert( transdist(dofvaluesold,_dofvaluesold) <= g_epsilon*len(dofvaluesold) )
                        dofvaluesnew = randlimits(*body.GetDOFLimits())
                        body.SetDOFValues(dofvaluesnew)
                        _dofvaluesnew = body.GetDOFValues()
                        assert( all(abs(body.SubtractDOFValues(dofvaluesnew,_dofvaluesnew)) <= g_epsilon) )
                        Tallnew,dofbranchesnew = body.GetLinkTransformations(True)
                        body.SetTransformWithDOFValues(body.GetTransform(),dofvaluesnew)
                        _Tallnew,dofbranchesnew = body.GetLinkTransformations(True)
                        assert( transdist(Tallnew,_Tallnew) <= g_epsilon*len(Tallnew) )
                        _dofvaluesnew = body.GetDOFValues()
                        assert( all(abs(body.SubtractDOFValues(dofvaluesnew,_dofvaluesnew)) <= g_epsilon) )
                        
                        # do it again
                        body.SetDOFValues(dofvaluesnew)
                        _Tallnew,_dofbranchesnew = body.GetLinkTransformations(True)
                        assert( transdist(Tallnew,_Tallnew) <= g_epsilon*len(Tallnew) )
                        assert( transdist(dofbranchesnew,_dofbranchesnew) == 0 )
                        for joint in body.GetJoints():
                            _dofvaluesnew = joint.GetValues()
                            assert( all(abs(joint.SubtractValues(dofvaluesnew[joint.GetDOFIndex():(joint.GetDOFIndex()+joint.GetDOF())], _dofvaluesnew)) <= g_epsilon) )
                        Tallnew2 = [randtrans() for link in body.GetLinks()]
                        for link,T in izip(body.GetLinks(),Tallnew2):
                            link.SetTransform(T)
                        _Tallnew2,_dofbranchesnew2 = body.GetLinkTransformations(True)
                        assert( transdist(Tallnew2, _Tallnew2) <= g_epsilon*len(Tallnew2) )
                        body.SetLinkTransformations(Tallnew,dofbranchesnew)
                        for idir in range(20):
                            deltavalues0 = array([g_jacobianstep*(random.randint(3)-1) for j in range(body.GetDOF())])
                            localtrans = randtrans()
                            for ilink,link in enumerate(body.GetLinks()):
                                jointchain = body.GetChain(0,link.GetIndex())
                                if len(jointchain) == 0:
                                    continue
                                body.SetDOFValues(dofvaluesnew)
                                Tlink = dot(link.GetTransform(),localtrans)
                                worldtrans = Tlink[0:3,3]
                                worldquat = quatFromRotationMatrix(Tlink[0:3,0:3]) # should use localquat
                                worldaxisangle = axisAngleFromRotationMatrix(Tlink[0:3,0:3])
                                Jtrans = body.CalculateJacobian(ilink,worldtrans)
                                Jquat = body.CalculateRotationJacobian(ilink,worldquat)
                                Jangvel = body.CalculateAngularVelocityJacobian(ilink)
                                body.SetDOFValues(dofvaluesnew+deltavalues0)
                                deltavalues = body.GetDOFValues()-dofvaluesnew
                                armlength = bodymaxjointdist(link,localtrans[0:3,3])
                                thresh = armlength*sum(abs(deltavalues))*1.1
                                if armlength < 0.0001 or thresh < 1e-12:
                                    continue
                                Tlinknew=dot(link.GetTransform(),localtrans)
                                newaxisangle = axisAngleFromRotationMatrix(Tlinknew[0:3,0:3])
                                newquat = quatFromRotationMatrix(Tlinknew[0:3,0:3])
                                if dot(worldquat,newquat) < 0:
                                    newquat = -newquat
                                deltatrans = Tlinknew[0:3,3] - worldtrans
                                if transdist(dot(Jtrans,deltavalues),deltatrans) > thresh:
                                    raise ValueError('jacobian failed name=%s,link=%s,dofvalues=%r, deltavalues=%r, computed=%r, newquat=%r'%(body.GetName(), link.GetName(), dofvaluesnew, deltavalues, dot(Jtrans,deltavalues), deltatrans))
                                if transdist(dot(Jquat,deltavalues)+worldquat,newquat) > 2*thresh:
                                    raise ValueError('jacobian failed name=%s,link=%s,dofvalues=%r, deltavalues=%r, computed=%r, newquat=%r'%(body.GetName(), link.GetName(), dofvaluesnew, deltavalues, dot(Jquat,deltavalues)+worldquat, newquat))
                                if axisangledist(dot(Jangvel,deltavalues)+worldaxisangle,newaxisangle) > 2*thresh:
                                    raise ValueError('jacobian failed name=%s,link=%s,dofvalues=%r, deltavalues=%r, angledist=%f, thresh=%f, armlength=%f'%(body.GetName(), link.GetName(), dofvaluesnew, deltavalues, axisangledist(dot(Jangvel,deltavalues)+worldaxisangle,newaxisangle), 2*thresh, armlength))

    def test_bodyvelocities(self):
        self.log.info('check physics/dynamics properties')
        with self.env:
            for envfile in g_envfiles:
                self.env.Reset()
                self.LoadEnv(envfile,{'skipgeometry':'1'})
                # try all loadable physics engines
                #self.env.SetPhysicsEngine()
                for i in range(10):
                    T = eye(4)
                    for body in self.env.GetBodies():
                        for ijoint,joint in enumerate(body.GetJoints()):
                            assert(joint.GetJointIndex()==ijoint and body.GetJointIndex(joint.GetName()) == ijoint )
                            assert(joint == body.GetJoint(joint.GetName()) )
                            assert(joint == body.GetJointFromDOFIndex(joint.GetDOFIndex()) )
                        # velocities, has to do with physics engine
                        oldlinkvels = body.GetLinkVelocities()
                        vellimits = body.GetDOFVelocityLimits()
                        dofvelnew = randlimits(-vellimits,vellimits)
                        link0vel = [random.rand(3)-0.5,random.rand(3)-0.5]
                        body.SetVelocity(*link0vel)
                        assert( all(abs(body.GetDOFVelocities()) <= g_epsilon ) )
                        body.SetDOFVelocities(dofvelnew,*link0vel,checklimits=True)
                        assert( transdist(body.GetDOFVelocities(),dofvelnew) <= g_epsilon )
                        linkvels = body.GetLinkVelocities()
                        newlinkvels = random.rand(len(body.GetLinks()),6)-0.5
                        for link,vel in izip(body.GetLinks(),newlinkvels):
                            link.SetVelocity(vel[0:3],vel[3:6])
                            assert( transdist(link.GetVelocity(),[vel[0:3],vel[3:6]]) <= g_epsilon )
                        assert( transdist(body.GetLinkVelocities(),newlinkvels) <= g_epsilon )
                        body.SetDOFVelocities(dofvelnew,linear=[0,0,0],angular=[0,0,0],checklimits=True)
                        assert( transdist(body.GetDOFVelocities(),dofvelnew) <= g_epsilon )
                        for link,vel in izip(body.GetLinks(),linkvels):
                            link.SetVelocity(vel[0:3],vel[3:6])
                        assert( transdist(body.GetLinkVelocities(),linkvels) <= g_epsilon and transdist(body.GetDOFVelocities(),dofvelnew) <= g_epsilon )
                        for joint in body.GetJoints():
                            assert( transdist(joint.GetVelocities(), dofvelnew[joint.GetDOFIndex():(joint.GetDOFIndex()+joint.GetDOF())]) <= g_epsilon )
                        for link,vel in izip(body.GetLinks(),linkvels):
                            assert( transdist(link.GetVelocity(),[vel[0:3],vel[3:6]]) <= g_epsilon )
                        # test consistency with kinematics

    def test_hierarchy(self):
        self.log.info('tests the kinematics hierarchy')
        with self.env:
            for robotfile in g_robotfiles:
                self.env.Reset()
                self.LoadEnv(robotfile,{'skipgeometry':'1'})
                body = self.env.GetBodies()[0]
                lowerlimit,upperlimit = body.GetDOFLimits()
                for i in range(len(lowerlimit)):
                    if upperlimit[i] - lowerlimit[i] > pi:
                        upperlimit[i] = lowerlimit[i]+pi
                body.SetDOFValues(lowerlimit)
                for ijoint,joint in enumerate(body.GetJoints()):
                    for ilink, link in enumerate(body.GetLinks()):
                        affect = body.DoesAffect(ijoint,ilink)
                        body.SetDOFValues([lowerlimit[joint.GetDOFIndex()]],[joint.GetDOFIndex()])
                        Tlink = link.GetTransform()
                        body.SetDOFValues([upperlimit[joint.GetDOFIndex()]],[joint.GetDOFIndex()])
                        Tlinknew = link.GetTransform()
                        if affect != 0 and not joint.IsStatic():
                            assert( lowerlimit[joint.GetDOFIndex()] < upperlimit[joint.GetDOFIndex()] )
                            assert( transdist(Tlink,Tlinknew) >= (upperlimit[joint.GetDOFIndex()]-lowerlimit[joint.GetDOFIndex()])*0.1 )
                        else:
                            assert( transdist(Tlink,Tlinknew) <= g_epsilon )
                body.SetDOFValues(lowerlimit)
                jointaxes0 = [joint.GetAxis(0) for joint in body.GetDependencyOrderedJoints()]
                jointanchors0 = [joint.GetAnchor() for joint in body.GetDependencyOrderedJoints()]
                assert( len(body.GetDependencyOrderedJoints()) == len(body.GetJoints()) )
                for ijoint in range(len(body.GetDependencyOrderedJoints())-1,0,-1):
                    joint = body.GetDependencyOrderedJoints()[ijoint]
                    body.SetDOFValues([upperlimit[joint.GetDOFIndex()]],[joint.GetDOFIndex()])
                    for ijoint2,joint2 in enumerate(body.GetDependencyOrderedJoints()[:ijoint]):
                        assert( transdist(joint2.GetAxis(0), jointaxes0[ijoint2]) <= g_epsilon )
                        assert( transdist(joint2.GetAnchor(), jointanchors0[ijoint2]) <= g_epsilon )
                for ilink0,ilink1 in combinations(range(len(body.GetLinks())),2):
                    link0 = body.GetLinks()[ilink0]
                    link1 = body.GetLinks()[ilink1]
                    jointchain = body.GetChain( ilink0, ilink1, returnjoints = True )
                    linkchain = body.GetChain( ilink0, ilink1, returnjoints = False )
                    assert( len(jointchain)+1 == len(linkchain) )
                    assert( jointchain[::-1] == body.GetChain( ilink1, ilink0, returnjoints = True ))
                    assert( linkchain[::-1] == body.GetChain( ilink1, ilink0, returnjoints = False ))
                    for ilink in range(len(linkchain)-1):
                        j = jointchain[ilink]
                        if j.GetDOFIndex() >= 0:
                            assert( body.IsDOFInChain(linkchain[ilink].GetIndex(),linkchain[ilink+1].GetIndex(),j.GetDOFIndex()) )
                        assert( linkchain[ilink].IsParentLink(linkchain[ilink+1]) or linkchain[ilink+1].IsParentLink(linkchain[ilink]) )
                        assert( linkchain[ilink] == j.GetHierarchyChildLink() or linkchain[ilink] == j.GetHierarchyParentLink())
                        assert( linkchain[ilink+1] == j.GetHierarchyChildLink() or linkchain[ilink+1] == j.GetHierarchyParentLink())

                #loops = body.GetClosedLoops()
                #for loop in loops:
                #    lknotindex = [i for i,(link,joint) in enumerate(loop) if link.GetIndex() == knot]
                #    lknownindex = [i for i,(link,joint) in enumerate(loop) if link == knownlink]

    def test_initkinbody(self):
        self.log.info('tests initializing a kinematics body')
        with self.env:
            k = RaveCreateKinBody(self.env,'')
            boxes = array(((0,0.5,0,0.1,0.2,0.3),(0.5,0,0,0.2,0.2,0.2)))
            k.InitFromBoxes(boxes,True)
            k.SetName('temp')
            self.env.AddKinBody(k)
            assert( len(k.GetLinks()) == 1 and len(k.GetLinks()[0].GetGeometries()) == 2 )
            assert( k.GetLinks()[0].GetGeometries()[0].GetType() == KinBody.Link.GeomProperties.Type.Box )
            assert( k.GetLinks()[0].GetGeometries()[1].GetType() == KinBody.Link.GeomProperties.Type.Box )
            k2 = RaveCreateKinBody(self.env,'')
            k2.InitFromTrimesh(TriMesh(*misc.ComputeBoxMesh([0.1,0.2,0.3])),True)
            k2.SetName('temp')
            self.env.AddKinBody(k2,True)
            assert( transdist(k2.ComputeAABB().extents(),[0.1,0.2,0.3]) <= g_epsilon )

    def test_misc(self):
        env=self.env
        body=env.ReadKinBodyURI('robots/pr2-beta-static.zae')
        env.AddKinBody(body)
        with env:
            s = 'this is a test string'
            body.SetUserData(s)
            assert(body.GetUserData()==s)
        
    def test_geometrychange(self):
        self.log.info('change geometry and test if changes are updated')
        env=self.env
        with env:
            self.LoadEnv(g_envfiles[0])
            for body in env.GetBodies():
                for link in body.GetLinks():
                    geom = link.GetGeometries()[0]
                    if geom.IsModifiable():
                        extents = [0.6,0.5,0.1]
                        geom.SetCollisionMesh(TriMesh(*misc.ComputeBoxMesh(extents)))
                        vmin = numpy.min(geom.GetCollisionMesh().vertices,0)
                        vmax = numpy.max(geom.GetCollisionMesh().vertices,0)
                        assert( transdist(0.5*(vmax-vmin),extents) <= g_epsilon )

    def test_hashes(self):
        robot = self.LoadRobot(g_robotfiles[0])
        s = robot.serialize(SerializationOptions.Kinematics)
        hash0 = robot.GetKinematicsGeometryHash()
        robot.SetLinkTransformations([randtrans() for link in robot.GetLinks()],zeros(robot.GetDOF()))
        hash1 = robot.GetKinematicsGeometryHash()
        assert( hash0 == hash1 )

    def test_staticlinks(self):
        env=self.env
        robot=self.LoadRobot('robots/barrettwam.robot.xml')
        with env:
            robot.SetDOFValues([0.5],[0])
            values = robot.GetDOFValues()
            anchors = [j.GetAnchor() for j in robot.GetJoints()]
            axes = [j.GetAxis(0) for j in robot.GetJoints()]
            Tlinks = robot.GetLinkTransformations()
            assert(not robot.GetLinks()[0].IsStatic())
            robot.SetDOFValues(zeros(robot.GetDOF()))
            robot.GetLinks()[0].SetStatic(True)
            assert(robot.GetLinks()[0].IsStatic())
            robot.SetDOFValues([0.5],[0])
            assert( transdist(values,robot.GetDOFValues()) <= g_epsilon )
            assert( transdist(Tlinks,robot.GetLinkTransformations()) <= g_epsilon )
            assert( transdist(anchors, [j.GetAnchor() for j in robot.GetJoints()]) <= g_epsilon )
            assert( transdist(axes, [j.GetAxis(0) for j in robot.GetJoints()]) <= g_epsilon )

    def test_jointoffset(self):
        env=self.env
        with env:
            for robotfile in g_robotfiles:
                env.Reset()
                self.LoadEnv(robotfile,{'skipgeometry':'1'})
                body = env.GetBodies()[0]

                zerovalues = zeros(body.GetDOF())
                body.SetDOFValues(zerovalues)
                Tlinks,dofbranches = body.GetLinkTransformations(True)
                limits = body.GetDOFLimits()
                limits = [numpy.maximum(-3*ones(body.GetDOF()),limits[0]), numpy.minimum(3*ones(body.GetDOF()),limits[1])]
                for myiter in range(10):
                    # todo set the first link to static
                    body.SetLinkTransformations(Tlinks,dofbranches)
                    body.SetZeroConfiguration()
                    assert( transdist(Tlinks,body.GetLinkTransformations()) <= g_epsilon )
                    assert( transdist(dofbranches,body.GetLinkTransformations(True)[1]) == 0 )
                    body.GetLinks()[0].SetStatic(myiter%2)
                    offsets = randlimits(*limits)
                    raveLogDebug(repr(offsets))
                    body.SetDOFValues(offsets)
                    Tlinksnew = body.GetLinkTransformations()
                    body.SetZeroConfiguration()
                    assert( transdist(zerovalues,body.GetDOFValues()) <= g_epsilon )
                    assert( transdist(Tlinksnew,body.GetLinkTransformations()) <= g_epsilon )
                    #body.SetDOFValues(-offsets,range(body.GetDOF()),checklimits=False)
                    #assert( transdist(Tlinksnew,body.GetLinkTransformations()) <= g_epsilon )
                    offsets = randlimits(*limits)
                    body.SetDOFValues(offsets)
                    assert( transdist(offsets,body.GetDOFValues()) <= g_epsilon )

    def test_wrapoffset(self):
        env=self.env
        with env:
            for robotfile in g_robotfiles:
                env.Reset()
                self.LoadEnv(robotfile,{'skipgeometry':'1'})
                body = env.GetBodies()[0]

                zerovalues = zeros(body.GetDOF())
                for i,offset in enumerate(zerovalues):
                    joint=body.GetJointFromDOFIndex(i)
                    joint.SetWrapOffset(offset,i-joint.GetDOFIndex())
                body.SetDOFValues(zerovalues)
                limits = body.GetDOFLimits()
                limits = [numpy.maximum(-3*ones(body.GetDOF()),limits[0]), numpy.minimum(3*ones(body.GetDOF()),limits[1])]
                for myiter in range(10):
                    body.GetLinks()[0].SetStatic(myiter%2)
                    body.SetDOFValues(zerovalues)
                    Tlinks = body.GetLinkTransformations()
                    offsets = randlimits(*limits)
                    raveLogDebug(repr(offsets))
                    for i,offset in enumerate(offsets):
                        joint=body.GetJointFromDOFIndex(i)
                        joint.SetWrapOffset(offset,i-joint.GetDOFIndex())

                    assert( transdist(zerovalues,body.GetDOFValues()) <= g_epsilon )
                    assert( transdist(Tlinks,body.GetLinkTransformations()) <= g_epsilon )
                    body.SetDOFValues(offsets)
                    assert( transdist(offsets,body.GetDOFValues()) <= g_epsilon )

    def test_joints(self):
        env=self.env
        xml = """
<kinbody name="universal">
  <body name="L0">
    <geom type="box">
      <extents>0.05 0.05 0.1</extents>
    </geom>
  </body>
  <body name="L1">
    <translation>0 0 0.3</translation>
    <geom type="box">
      <extents>0.05 0.05 0.1</extents>
    </geom>
  </body>
  <joint type="%s" name="J0">
    <body>L0</body>
    <body>L1</body>
    <axis1>1 0 0</axis1>
    <axis2>0 1 0</axis2>
    <anchor>0 0 0.2</anchor>
  </joint>
</kinbody>
"""
        with env:
#             body = env.ReadKinBodyData(xml%'universal')
#             env.AddKinBody(body)
#             assert(body.GetDOF()==2)
#             assert(len(body.GetJoints())==1)
#             assert(env.GetJoints()[0].GetType()==Joint.Type.Universal)
            env.Reset()
            body = env.ReadKinBodyData(xml%'hinge2')
            env.AddKinBody(body)
            assert(body.GetDOF()==2)
            assert(len(body.GetJoints())==1)
            assert(body.GetJoints()[0].GetType()==KinBody.Joint.Type.Hinge2)

    def test_mimicjoints(self):
        env=self.env
        xml="""
<kinbody name="a">
  <body name="L0">
  </body>
  <body name="L1">
  </body>
  <body name="L2">
  </body>
  <body name="L3">
  </body>
  <joint name="J0" type="hinge">
    <body>L0</body>
    <body>L1</body>
    <axis>1 0 0</axis>
  </joint>
  <joint name="J0a" type="hinge" mimic_pos="2*J0" mimic_vel="|J0 2" mimic_accel="|J0 0">
    <body>L1</body>
    <body>L2</body>
    <axis>1 0 0</axis>
  </joint>
  <joint name="J0b" type="hinge" mimic_pos="2*J0a+J0" mimic_vel="|J0a 2 |J0 1" mimic_accel="|J0a 0 |J0 0">
    <body>L2</body>
    <body>L3</body>
    <axis>1 0 0</axis>
  </joint>
</kinbody>
"""
        body = env.ReadKinBodyData(xml)
        env.AddKinBody(body)
        assert(len(body.GetJoints())==1)
        assert(len(body.GetPassiveJoints())==2)
        value = 0.5
        body.SetDOFValues([value])
        J0a = body.GetJoint('J0a')
        J0b = body.GetJoint('J0b')
        assert(abs(J0a.GetValues()[0]-2*value) <= g_epsilon )
        assert(abs(J0b.GetValues()[0]-5*value) <= g_epsilon )
        assert(J0a.GetMimicDOFIndices() == [0])
        assert(J0b.GetMimicDOFIndices() == [0])

    def test_specification(self):
        env=self.env
        self.LoadEnv('data/lab1.env.xml')
        robot=env.GetRobots()[0]
        spec=robot.GetConfigurationSpecification()
        s=pickle.dumps(spec)
        newspec=pickle.loads(s)
        assert(newspec==spec)

    def test_inertia(self):
        env=self.env
        massdensity=2.5
        massxml = """<mass type="mimicgeom">
          <density>%f</density>
        </mass>
        """%massdensity
        xmldata = """<kinbody name="test">
        %(mass)s
        <body name="box">
          <geom type="box">
            <extents>1 2 3</extents>
          </geom>
        </body>
        <body name="rbox">
          <rotationaxis>0 1 0 45</rotationaxis>
          <translation>1 2 3</translation>
          <geom type="box">
            <rotationaxis>1 0 0 45</rotationaxis>
            <translation>0.5 1.5 2.5</translation>
            <extents>1 2 3</extents>
          </geom>
        </body>
        <body name="sphere">
          <geom type="sphere">
            <radius>0.5</radius>
          </geom>
        </body>
        <body name="cylinder">
          <geom type="cylinder">
            <height>2</height>
            <radius>0.2</radius>
          </geom>
        </body>
        </kinbody>"""%{'mass':massxml}
        body = env.ReadKinBodyXMLData(xmldata)
        env.AddKinBody(body)
        m = body.GetLink('box').GetMass()
        assert(abs(m-48*massdensity) <= g_epsilon)
        assert(transdist(body.GetLink('box').GetLocalMassFrame(),eye(4)) <= g_epsilon)
        inertia = m/12*array([4+9,1+9,1+4])
        assert(transdist(body.GetLink('box').GetPrincipalMomentsOfInertia(),inertia) <= g_epsilon)

        m = body.GetLink('rbox').GetMass()
        assert(abs(m-48*massdensity) <= g_epsilon)
        R = rotationMatrixFromAxisAngle([pi/4,0,0])
        I=dot(R,dot(diag(inertia),transpose(R)))
        assert(transdist(body.GetLink('rbox').GetLocalInertia(),I) <= g_epsilon)
        assert(transdist(body.GetLink('rbox').GetLocalCOM(),[0.5, 1.5, 2.5]) <= g_epsilon)
        
        m = body.GetLink('sphere').GetMass()
        assert(abs(m-4.0/3*pi*0.5**3*massdensity) <= g_epsilon)
        assert(transdist(body.GetLink('sphere').GetLocalMassFrame(),eye(4)) <= g_epsilon)
        assert(transdist(body.GetLink('sphere').GetPrincipalMomentsOfInertia(),0.4*m*0.5**2*ones(3)) <= g_epsilon)
        m = body.GetLink('cylinder').GetMass()
        assert(abs(m-massdensity*pi*0.2**2*2) <= g_epsilon)
        assert(transdist(body.GetLink('cylinder').GetLocalMassFrame(),eye(4)) <= g_epsilon)
        assert(transdist(body.GetLink('cylinder').GetPrincipalMomentsOfInertia(), m/12*array([3*0.2**2+2**2,6*0.2**2,3*0.2**2+2**2])) <= g_epsilon)

    def test_dh(self):
        env=self.env
        robot=self.LoadRobot('robots/barrettwam.robot.xml')
        dhs=planningutils.GetDHParameters(robot)
        gooddhs = [planningutils.DHParameter(joint=robot.GetJoint('Shoulder_Yaw'), parentindex=-1, d=0.346000, a=0.260768, theta=0.566729, alpha=0.000000,transform=array([[ 0.84366149, -0.53687549,  0.        ,  0.22      ],[ 0.53687549,  0.84366149,  0.        ,  0.14      ], [ 0.        ,  0.        ,  1.        ,  0.346     ], [ 0.        ,  0.        ,  0.        ,  1.        ]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Shoulder_Pitch'), parentindex=0, d=0.000000, a=0.000000, theta=-0.566729, alpha=-1.570796,transform=array([[  1.00000000e+00,  -2.46519033e-32,  -1.11022302e-16, 2.20000000e-01], [  1.11022302e-16,   2.22044605e-16,   1.00000000e+00, 1.40000000e-01], [  0.00000000e+00,  -1.00000000e+00,   2.22044605e-16, 3.46000000e-01], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Shoulder_Roll'), parentindex=1, d=0.000000, a=0.000000, theta=0.000000, alpha=1.570796,transform=array([[  1.00000000e+00,  -1.11022302e-16,  -6.16297582e-32, 2.20000000e-01], [  1.11022302e-16,   1.00000000e+00,   5.55111512e-16, 1.40000000e-01], [  0.00000000e+00,  -5.55111512e-16,   1.00000000e+00, 3.46000000e-01], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Elbow'), parentindex=2, d=0.550000, a=0.045000, theta=0.000000, alpha=-1.570796,transform=array([[  1.00000000e+00,  -2.46519033e-32,  -1.11022302e-16, 2.65000000e-01], [  1.11022302e-16,   2.22044605e-16,   1.00000000e+00, 1.40000000e-01], [  0.00000000e+00,  -1.00000000e+00,   2.22044605e-16, 8.96000000e-01], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Wrist_Yaw'), parentindex=3, d=-0.000000, a=-0.045000, theta=0.000000, alpha=1.570796,transform=array([[  1.00000000e+00,  -1.11022302e-16,  -4.93038066e-32, 2.20000000e-01], [  1.11022302e-16,   1.00000000e+00,   4.44089210e-16, 1.40000000e-01], [  0.00000000e+00,  -4.44089210e-16,   1.00000000e+00, 8.96000000e-01], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Wrist_Pitch'), parentindex=4, d=0.300000, a=-0.000000, theta=0.000000, alpha=-1.570796, transform=array([[  1.00000000e+00,  -4.93038066e-32,  -1.11022302e-16,
          2.20000000e-01], [  1.11022302e-16,   4.44089210e-16,   1.00000000e+00, 1.40000000e-01], [  0.00000000e+00,  -1.00000000e+00,   4.44089210e-16,           1.19600000e+00], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('Wrist_Roll'), parentindex=5, d=-0.000000, a=0.000000, theta=0.000000, alpha=1.570796, transform=array([[  1.00000000e+00,  -1.11022302e-16,  -4.93038066e-32,
          2.20000000e-01],[  1.11022302e-16,   1.00000000e+00,   4.44089210e-16, 1.40000000e-01], [  0.00000000e+00,  -4.44089210e-16,   1.00000000e+00, 1.19600000e+00], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('JF3'), parentindex=6, d=0.151500, a=-0.050000, theta=0.000000, alpha=-1.570796, transform=array([[  1.00000000e+00,  -4.93038066e-32,  -1.11022302e-16,
          1.70000000e-01], [  1.11022302e-16,   4.44089210e-16,   1.00000000e+00, 1.40000000e-01], [  0.00000000e+00,  -1.00000000e+00,   4.44089210e-16, 1.34750000e+00], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('JF4'), parentindex=6, d=0.151500, a=-0.000000, theta=0.000000, alpha=-3.141593, transform=array([[  1.00000000e+00,   1.11022302e-16,  -1.35963107e-32,
          2.20000000e-01], [  1.11022302e-16,  -1.00000000e+00,   1.22464680e-16, 1.40000000e-01], [  0.00000000e+00,  -1.22464680e-16,  -1.00000000e+00, 1.34750000e+00], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]])),
                  planningutils.DHParameter(joint=robot.GetJoint('JF1'), parentindex=8, d=0.000000, a=0.050000, theta=0.000000, alpha=-1.570796, transform=array([[  1.00000000e+00,  -2.46519033e-32,   1.11022302e-16,
          2.70000000e-01], [  1.11022302e-16,   2.22044605e-16,  -1.00000000e+00, 1.40000000e-01], [  0.00000000e+00,   1.00000000e+00,   2.22044605e-16, 1.34750000e+00], [  0.00000000e+00,   0.00000000e+00,   0.00000000e+00, 1.00000000e+00]]))]
        
        for i,gooddh in enumerate(gooddhs):
            dh=dhs[i]
            assert(transdist(dh.transform,gooddh.transform) <= 1e-6)
            assert(dh.joint == gooddh.joint)
            assert(abs(dh.a-gooddh.a) <= 1e-6)
            assert(abs(dh.d-gooddh.d) <= 1e-6)
            assert(abs(dh.alpha-gooddh.alpha) <= 1e-6)
            assert(abs(dh.theta-gooddh.theta) <= 1e-6)

    def test_closedlinkage(self):
        self.log.info('check a very complex closed linkage model')
        env=self.env
        self.LoadEnv('testdata/bobcat.robot.xml')
        robot=env.GetRobots()[0]
        with env:
            Ajoint = robot.GetJoint('A')
            Ljoint = robot.GetJoint('L')
            assert(Ajoint.GetDOF() == 1 and Ljoint.GetDOF() == 1)
            dofindices = [Ajoint.GetDOFIndex(), Ljoint.GetDOFIndex()]
            robot.SetActiveDOFs(dofindices)
            linkdata = [[ [0,0], array([[  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   0.00000000e+00,   0.00000000e+00, -6.50000000e-01],
                                         [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,   6.20000000e-01, -1.01100000e+00],
                                         [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,   6.20000000e-01, -1.01100000e+00],
                                         [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                         [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                         [  1.00000000e+00,   0.00000000e+00,   1.66533454e-16, 2.46519033e-32,   1.25704890e-01,  -2.48984221e-32, -4.36358840e-01],
                                         [  6.85227643e-01,   6.85227643e-01,   1.74536749e-01, -1.74536749e-01,   3.69363050e-01,   1.68017796e-18, -1.17973100e-01],
                                         [  9.84549793e-01,   4.84676144e-27,   1.75104840e-01, -6.20658774e-18,  -7.65520000e-01,   0.00000000e+00, -8.86520000e-01],
                                         [  9.84549793e-01,   4.84676144e-27,   1.75104840e-01, -6.20658774e-18,  -7.65520000e-01,   0.00000000e+00, -8.86520000e-01],
                                         [  9.54793018e-01,   8.25093916e-18,   2.97271412e-01, 1.25474580e-18,  -8.44224080e-01,   0.00000000e+00, 1.68398220e-01],
                                         [  1.00000000e+00,   5.20417043e-17,  -4.32015615e-06, -4.16333634e-17,   9.30169191e-01,  -2.75764047e-17, -4.80552929e-01],
                                         [  1.00000000e+00,   5.20417043e-17,  -4.32015615e-06, -4.16333634e-17,   1.33400753e+00,  -2.04263127e-17, -8.72316290e-01],
                                         [  5.31460156e-01,   5.31460156e-01,  -4.66422665e-01, 4.66422665e-01,   1.33400414e+00,   1.50396600e-16, -1.05231978e+00],
                                         [  6.86988988e-01,   6.86988988e-01,  -1.67469790e-01, 1.67469790e-01,   1.38471499e+00,   7.72830067e-18, -5.97523487e-01]])],
                         [ [0.2,0.15], array([[  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   0.00000000e+00,   0.00000000e+00, -6.50000000e-01],
                                              [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,   6.20000000e-01, -1.01100000e+00],
                                            [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,   6.20000000e-01, -1.01100000e+00],
                                              [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                              [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                              [  9.88182137e-01,   0.00000000e+00,   1.53284259e-01, 2.77555756e-17,   1.49435915e-01,  -2.80331312e-17, -2.83371348e-01],
                                              [  7.06794528e-01,   7.06794528e-01,   2.10117950e-02, -2.10117950e-02,   2.10279270e-01,   1.22666523e-18, 4.76223716e-01],
                                              [  9.95574100e-01,   1.73472348e-18,   9.39798451e-02, -6.93889390e-18,  -7.65520000e-01,   0.00000000e+00, -8.86520000e-01],
                                              [  9.95574100e-01,   1.73472348e-18,   9.39798451e-02, -6.93889390e-18,  -7.28094440e-01,  -2.54446008e-17, -6.90052885e-01],
                                              [  9.99520409e-01,   6.93889390e-18,   3.09669378e-02, -2.77555756e-17,  -9.82177231e-01,   7.63757772e-19, 2.16000404e-01],
                                              [  9.67858375e-01,  -2.60208521e-18,  -2.51495859e-01, -1.21430643e-17,   8.72051279e-01,  -7.74527579e-17, 3.86638746e-01],
                                              [  9.67858375e-01,  -2.60208521e-18,  -2.51495859e-01, -1.21430643e-17,   1.56045196e+00,  -9.43376201e-17, 2.02355294e-01],
                                              [  6.23592186e-01,   6.23592186e-01,  -3.33365844e-01, 3.33365844e-01,   1.48074579e+00,  -3.52546462e-17, 4.09640579e-02],
                                              [  7.07073309e-01,   7.07073309e-01,  -6.88009992e-03, 6.88009992e-03,   1.72761367e+00,   1.03884658e-16, 4.26278877e-01]])],
                         [ [0.6,0.3], array([[  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   0.00000000e+00,   0.00000000e+00, -6.50000000e-01],
                                             [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,   6.20000000e-01, -1.01100000e+00],
                                             [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,   6.20000000e-01, -1.01100000e+00],
                                             [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,   7.69000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                             [  1.00000000e+00,   0.00000000e+00,   0.00000000e+00, 0.00000000e+00,  -2.61000000e-01,  -6.20000000e-01, -1.01100000e+00],
                                             [  8.63508551e-01,   0.00000000e+00,   5.04334197e-01, 1.11022302e-16,   3.82601401e-01,  -8.40993932e-17, 3.49301605e-03],
                                             [  6.60498754e-01,   6.60498754e-01,  -2.52470583e-01, 2.52470583e-01,   8.54405236e-02,  -2.38637001e-16, 1.25541132e+00],
                                             [  9.83185295e-01,  -2.16840434e-19,   1.82610721e-01, -2.16840434e-18,  -7.65520000e-01,   0.00000000e+00, -8.86520000e-01],
                                             [  9.83185295e-01,  -2.16840434e-19,   1.82610721e-01, -2.16840434e-18,  -5.50071789e-01,  -7.36981434e-17, -3.26536011e-01],
                                             [  9.72102789e-01,   1.04083409e-17,   2.34555254e-01, -1.04083409e-17,  -8.74679979e-01,   5.97978576e-17, 1.86574033e-01],
                                             [  8.41280342e-01,  -7.63278329e-17,  -5.40599100e-01, -1.11022302e-16,   6.15005480e-01,  -4.15705803e-16, 1.66226340e+00],
                                             [  8.41280342e-01,  -7.63278329e-17,  -5.40599100e-01, -1.11022302e-16,   1.41851038e+00,  -6.29478324e-16, 1.97615467e+00],
                                             [  6.71448444e-01,   6.71448444e-01,  -2.21713751e-01, 2.21713751e-01,   1.28904974e+00,  -4.73379676e-16, 1.85111343e+00],
                                             [  6.97817029e-01,   6.97817029e-01,   1.14242700e-01, -1.14242700e-01,   1.65140668e+00,  -3.55752435e-16, 2.13059278e+00]])],
                         ]

            for dofvalues, linkposes in linkdata:
                robot.SetActiveDOFValues(dofvalues)
                curposes = poseFromMatrices(robot.GetLinkTransformations())
                assert( transdist(linkposes,curposes) <= 1e-6 )
